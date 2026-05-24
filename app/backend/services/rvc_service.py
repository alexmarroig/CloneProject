from __future__ import annotations

import json
import os
import subprocess
import threading
import atexit
import logging
from pathlib import Path
from typing import Any

from app.backend.core.runtime import format_device_for_framework, resolve_device, resolve_python
from app.backend.core.settings import settings

logger = logging.getLogger(__name__)


class RVCService:
    def __init__(self) -> None:
        self._daemon_lock = threading.RLock()
        self._convert_daemon: subprocess.Popen[str] | None = None
        self._daemon_gpu_index: str | None = None
        self._daemon_device: str | None = None
        atexit.register(self._stop_convert_daemon)

    def _daemon_command(self) -> list[str]:
        # Use simplified worker that doesn't require fairseq imports
        worker_script = settings.app_dir / "backend" / "workers" / "rvc_worker_simple.py"
        return [resolve_python(settings.rvc_env_python), str(worker_script), "--daemon"]

    def _daemon_env(self, payload: dict[str, Any]) -> dict[str, str]:
        environment = os.environ.copy()
        if payload.get("device") == "cuda" and payload.get("gpu_index") is not None:
            environment["CUDA_VISIBLE_DEVICES"] = str(payload["gpu_index"])

        # Set RVC-specific environment variables
        environment["weight_root"] = str(settings.rvc_weights_dir)
        environment["rmvpe_root"] = str(settings.app_dir.parent / "assets" / "rmvpe")

        # Ensure FFmpeg is in PATH
        ffmpeg_dir = settings.app_dir.parent
        if str(ffmpeg_dir) not in environment.get("PATH", ""):
            environment["PATH"] = f"{ffmpeg_dir}{os.pathsep}{environment.get('PATH', '')}"

        return environment

    def _ensure_convert_daemon(self, payload: dict[str, Any]) -> subprocess.Popen[str]:
        requested_device = str(payload.get("device", "cpu"))
        requested_gpu = str(payload.get("gpu_index")) if payload.get("gpu_index") is not None else None
        process = self._convert_daemon
        if process is not None and process.poll() is None:
            if self._daemon_device == requested_device and self._daemon_gpu_index == requested_gpu:
                return process
            self._stop_convert_daemon()
        process = subprocess.Popen(  # noqa: S603
            self._daemon_command(),
            cwd=str(settings.rvc_root_dir),
            env=self._daemon_env(payload),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        self._convert_daemon = process
        self._daemon_device = requested_device
        self._daemon_gpu_index = requested_gpu
        return process

    def _stop_convert_daemon(self) -> None:
        process = self._convert_daemon
        self._convert_daemon = None
        self._daemon_device = None
        self._daemon_gpu_index = None
        if process is None:
            return
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except Exception:
                process.kill()

    def _readline_with_timeout(self, stream, timeout: int | None) -> str:
        result: dict[str, str] = {}
        error: dict[str, Exception] = {}

        def worker() -> None:
            try:
                line = stream.readline()
                result["line"] = line
            except Exception as exc:  # pragma: no cover - defensive
                error["exception"] = exc

        reader = threading.Thread(target=worker, daemon=True)
        reader.start()
        reader.join(timeout)
        if reader.is_alive():
            raise TimeoutError("RVC convert daemon response timed out")
        if "exception" in error:
            raise RuntimeError(str(error["exception"]))
        return result.get("line", "")

    def _run_convert_daemon(self, payload: dict[str, Any], timeout: int | None = None) -> str:
        """Run RVC conversion directly via subprocess to avoid fairseq import issues in main process"""
        try:
            # Build command for infer_cli.py with correct argument names
            input_path = Path(payload["input_path"])
            output_path = Path(payload["output_path"])
            model_path = Path(payload["model_path"])
            index_path = payload.get("index_path")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Extract model name from path (e.g., "api_probe4" from ".../api_probe4/model.pth")
            model_name = model_path.parent.name if model_path.name == "model.pth" else model_path.stem

            cmd = [
                str(resolve_python(settings.rvc_env_python)),
                str(settings.rvc_root_dir / "tools" / "infer_cli.py"),
                "--model_name", model_name,
                "--input_path", str(input_path),
                "--opt_path", str(output_path),
                "--device", payload.get("torch_device", "cpu"),
                "--f0up_key", str(payload.get("pitch_shift", 0)),
                "--f0method", payload.get("f0_method", "rmvpe"),
                "--index_rate", str(payload.get("index_rate", 0.66)),
                "--filter_radius", str(payload.get("filter_radius", 3)),
                "--resample_sr", str(payload.get("resample_rate", 0)),
                "--rms_mix_rate", str(payload.get("rms_mix_rate", 1.0)),
                "--protect", str(payload.get("protect_consonants", 0.33)),
            ]

            if index_path and Path(index_path).exists():
                cmd.extend(["--index_path", str(index_path)])

            # Log command for debugging
            logger.info(f"RVC command: {' '.join(cmd)}")
            logger.info(f"Working directory: {settings.rvc_root_dir}")
            logger.info(f"Model name extracted: {model_name}")
            logger.info(f"Input path: {input_path} (exists: {input_path.exists()})")
            logger.info(f"Expected output path: {output_path}")

            # Prepare environment with FFmpeg and required paths for RVC
            env = os.environ.copy()

            # Add FFmpeg to PATH
            ffmpeg_dir = settings.app_dir.parent
            if str(ffmpeg_dir) not in env.get("PATH", ""):
                env["PATH"] = f"{ffmpeg_dir}{os.pathsep}{env.get('PATH', '')}"
                logger.info(f"Added FFmpeg dir to PATH: {ffmpeg_dir}")

            # Set RVC weight_root for model loading
            env["weight_root"] = str(settings.rvc_weights_dir)
            logger.info(f"Set weight_root: {settings.rvc_weights_dir}")

            # Set RMVPE root for pitch extraction
            rmvpe_root = settings.app_dir.parent / "assets" / "rmvpe"
            if rmvpe_root.exists():
                env["rmvpe_root"] = str(rmvpe_root)
                logger.info(f"Set rmvpe_root: {rmvpe_root}")

            # Run conversion in isolated subprocess
            completed = subprocess.run(
                cmd,
                cwd=str(settings.rvc_root_dir),
                capture_output=True,
                text=True,
                timeout=timeout or 300,
                check=False,
                env=env
            )

            # Log subprocess output regardless of returncode
            logger.info(f"RVC returncode: {completed.returncode}")
            if completed.stdout:
                logger.info(f"RVC stdout:\n{completed.stdout}")
            if completed.stderr:
                logger.warning(f"RVC stderr:\n{completed.stderr}")

            if completed.returncode != 0:
                error_msg = completed.stderr if completed.stderr else completed.stdout
                raise RuntimeError(f"RVC conversion failed: {error_msg.strip()}")

            if not output_path.exists():
                raise RuntimeError(f"RVC did not create output file at {output_path}")

            # Check for 0-byte files (symptom of incomplete/failed conversion)
            file_size = output_path.stat().st_size
            if file_size == 0:
                logger.error(f"RVC created 0-byte output file at {output_path}")
                raise RuntimeError(f"RVC conversion produced empty file (0 bytes) at {output_path}")

            result = {
                "output_path": str(output_path),
                "success": True,
                "file_size": file_size
            }
            return json.dumps(result, ensure_ascii=False)

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"RVC conversion timed out after {timeout or 300} seconds")
        except Exception as e:
            raise RuntimeError(f"RVC conversion failed: {str(e)}")

    def _run_worker(self, payload: dict[str, Any], timeout: int | None = None) -> str:
        command = [resolve_python(settings.rvc_env_python), str(settings.rvc_worker_script), json.dumps(payload)]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            cwd=str(settings.rvc_root_dir),
            env=self._daemon_env(payload),
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "RVC worker failed")
        return completed.stdout.strip()

    def convert_voice(
        self,
        *,
        input_path: Path,
        output_path: Path,
        model_path: Path,
        index_path: Path,
        pitch_shift: int,
        index_rate: float,
        f0_method: str = "rmvpe",
        filter_radius: int = 3,
        resample_rate: int = 0,
        rms_mix_rate: float = 1.0,
        protect_consonants: float = 0.33,
        gpu_device: str = "auto",
        use_gpu: bool = True,
        timeout: int | None = None,
    ) -> Path:
        resolved_device, gpu_index = resolve_device(
            use_gpu=use_gpu,
            requested_device=gpu_device,
            requested_gpu_index=gpu_device,
        )
        payload = {
            "mode": "convert",
            "input_path": str(input_path),
            "output_path": str(output_path),
            "model_path": str(model_path),
            "index_path": str(index_path),
            "pitch_shift": pitch_shift,
            "index_rate": index_rate,
            "f0_method": f0_method,
            "filter_radius": filter_radius,
            "resample_rate": resample_rate,
            "rms_mix_rate": rms_mix_rate,
            "protect_consonants": protect_consonants,
            "device": resolved_device,
            "gpu_index": gpu_index,
            "torch_device": format_device_for_framework(resolved_device, gpu_index),
            "enable_cache": True,
        }
        self._run_convert_daemon(payload, timeout=timeout)
        return output_path

    def preprocess(
        self,
        *,
        voice_name: str,
        dataset_path: str,
        sample_rate: str,
        silence_slicing: bool,
        normalize: bool,
        min_audio_seconds: float,
        max_audio_seconds: float,
        timeout: int | None = None,
    ) -> None:
        payload = {
            "mode": "preprocess",
            "voice_name": voice_name,
            "dataset_path": dataset_path,
            "sample_rate": sample_rate,
            "silence_slicing": silence_slicing,
            "normalize": normalize,
            "min_audio_seconds": min_audio_seconds,
            "max_audio_seconds": max_audio_seconds,
        }
        self._run_worker(payload, timeout=timeout)

    def extract_pitch(self, *, voice_name: str, f0_method: str, timeout: int | None = None) -> None:
        payload = {"mode": "extract_pitch", "voice_name": voice_name, "f0_method": f0_method}
        self._run_worker(payload, timeout=timeout)

    def extract_features(
        self,
        *,
        voice_name: str,
        version: str,
        use_gpu: bool,
        gpu_device: str = "auto",
        timeout: int | None = None,
    ) -> None:
        resolved_device, gpu_index = resolve_device(
            use_gpu=use_gpu,
            requested_device=gpu_device,
            requested_gpu_index=gpu_device,
        )
        payload = {
            "mode": "extract_features",
            "voice_name": voice_name,
            "version": version,
            "device": resolved_device,
            "gpu_index": gpu_index,
            "torch_device": format_device_for_framework(resolved_device, gpu_index),
        }
        self._run_worker(payload, timeout=timeout)

    def train(
        self,
        *,
        voice_name: str,
        sample_rate: str,
        epochs: int,
        batch_size: int,
        learning_rate: float,
        save_every_epoch: int,
        mixed_precision: bool,
        version: str,
        use_gpu: bool,
        gpu_device: str = "auto",
        timeout: int | None = None,
    ) -> dict[str, Any]:
        resolved_device, gpu_index = resolve_device(
            use_gpu=use_gpu,
            requested_device=gpu_device,
            requested_gpu_index=gpu_device,
        )
        payload = {
            "mode": "train",
            "voice_name": voice_name,
            "sample_rate": sample_rate,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "save_every_epoch": save_every_epoch,
            "mixed_precision": mixed_precision,
            "version": version,
            "device": resolved_device,
            "gpu_index": gpu_index,
            "torch_device": format_device_for_framework(resolved_device, gpu_index),
        }
        return json.loads(self._run_worker(payload, timeout=timeout))

    def build_index(self, *, voice_name: str, version: str, timeout: int | None = None) -> dict[str, Any]:
        payload = {"mode": "build_index", "voice_name": voice_name, "version": version}
        return json.loads(self._run_worker(payload, timeout=timeout))


rvc_service = RVCService()
