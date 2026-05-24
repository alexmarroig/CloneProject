from __future__ import annotations

import re
import subprocess
from pathlib import Path

from app.backend.core.settings import settings
from app.backend.models.schemas import GpuUsage, JobLogsResponse, TrainingMetricPoint
from app.backend.services.job_manager import job_manager


_LOSS_PATTERN = re.compile(
    r"loss_disc=(?P<loss_disc>[-+]?\d*\.?\d+),\s*"
    r"loss_gen=(?P<loss_gen>[-+]?\d*\.?\d+),\s*"
    r"loss_fm=(?P<loss_fm>[-+]?\d*\.?\d+),\s*"
    r"loss_mel=(?P<loss_mel>[-+]?\d*\.?\d+),\s*"
    r"loss_kl=(?P<loss_kl>[-+]?\d*\.?\d+)"
)


class LogService:
    def _tail(self, path: Path, max_lines: int = 300) -> str:
        if not path.exists():
            return ""
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        return "\n".join(lines[-max_lines:])

    def _gpu_usage(self) -> GpuUsage | None:
        try:
            command = [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ]
            output = subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL, timeout=2)
            first = output.splitlines()[0]
            name, utilization, mem_used, mem_total = [item.strip() for item in first.split(",")]
            return GpuUsage(
                gpu_name=name,
                utilization_percent=float(utilization),
                memory_used_mb=float(mem_used),
                memory_total_mb=float(mem_total),
            )
        except Exception:
            return None

    def _parse_metrics(self, train_log: str) -> list[TrainingMetricPoint]:
        metrics: list[TrainingMetricPoint] = []
        for idx, line in enumerate(train_log.splitlines(), start=1):
            match = _LOSS_PATTERN.search(line)
            if not match:
                continue
            metrics.append(
                TrainingMetricPoint(
                    step=idx,
                    loss_disc=float(match.group("loss_disc")),
                    loss_gen=float(match.group("loss_gen")),
                    loss_fm=float(match.group("loss_fm")),
                    loss_mel=float(match.group("loss_mel")),
                    loss_kl=float(match.group("loss_kl")),
                )
            )
        return metrics[-120:]

    def job_logs(self, job_id: str) -> JobLogsResponse:
        job = job_manager.get_job(job_id)
        if job is None:
            raise FileNotFoundError(job_id)
        voice_name = job.payload.get("voice_name")
        logs: dict[str, str] = {}
        metrics: list[TrainingMetricPoint] = []
        if voice_name:
            exp_dir = settings.rvc_root_dir / "logs" / voice_name
            preprocess_log = self._tail(exp_dir / "preprocess.log")
            extract_log = self._tail(exp_dir / "extract_f0_feature.log")
            train_log = self._tail(exp_dir / "train.log")
            logs = {
                "preprocess.log": preprocess_log,
                "extract_f0_feature.log": extract_log,
                "train.log": train_log,
            }
            metrics = self._parse_metrics(train_log)
        return JobLogsResponse(
            job_id=job_id,
            voice_name=voice_name,
            logs=logs,
            metrics=metrics,
            gpu=self._gpu_usage(),
            events=job_manager.list_events(job_id, since_id=0, limit=1000),
        )


log_service = LogService()
