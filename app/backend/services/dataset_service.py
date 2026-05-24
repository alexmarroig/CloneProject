from __future__ import annotations

import json
import wave
from pathlib import Path
import subprocess

from app.backend.core.paths import assert_extension, resolve_inside, sanitize_name
from app.backend.core.runtime import ffmpeg_binary
from app.backend.core.settings import settings
from app.backend.core.timeutils import utc_now_iso
from app.backend.models.schemas import DatasetDetails, DatasetFileInfo, DatasetPrepareResponse, DatasetSummary


_AUDIO_EXTENSIONS = set(settings.allowed_audio_extensions)


class DatasetService:
    def __init__(self) -> None:
        self.datasets_dir = settings.datasets_dir
        self.preprocessed_dir = settings.datasets_preprocessed_dir

    def _safe_dataset_dir(self, dataset_name: str) -> Path:
        safe_name = sanitize_name(dataset_name, "dataset_name")
        return resolve_inside(self.datasets_dir, safe_name, "dataset_name")

    def _resolve_dataset_path(self, dataset_path: str) -> Path:
        candidate = Path(dataset_path)
        for base in (self.datasets_dir, self.preprocessed_dir):
            try:
                return resolve_inside(base, candidate, "dataset_path", must_exist=True)
            except Exception:
                continue
        raise ValueError("dataset_path must resolve inside runtime datasets directories")

    def _iter_audio_files(self, dataset_path: Path) -> list[Path]:
        if not dataset_path.exists() or not dataset_path.is_dir():
            return []
        return [item for item in sorted(dataset_path.iterdir()) if item.is_file() and item.suffix.lower() in _AUDIO_EXTENSIONS]

    def _duration_seconds(self, path: Path) -> float | None:
        if path.suffix.lower() != ".wav":
            return None
        try:
            with wave.open(str(path), "rb") as wav:
                frames = wav.getnframes()
                rate = wav.getframerate() or 1
            return round(frames / float(rate), 4)
        except Exception:
            return None

    def _summary(self, dataset_path: Path) -> DatasetSummary:
        files = self._iter_audio_files(dataset_path)
        total_bytes = sum(file.stat().st_size for file in files)
        total_seconds = sum(self._duration_seconds(file) or 0.0 for file in files)
        return DatasetSummary(
            name=dataset_path.name,
            path=str(dataset_path),
            file_count=len(files),
            total_bytes=total_bytes,
            total_duration_seconds=round(total_seconds, 4),
            updated_at=utc_now_iso(),
        )

    def list_datasets(self) -> list[DatasetSummary]:
        datasets: list[DatasetSummary] = []
        for item in sorted(self.datasets_dir.iterdir()):
            if item.is_dir():
                datasets.append(self._summary(item))
        return datasets

    def dataset_details(self, dataset_name: str) -> DatasetDetails:
        dataset_path = self._safe_dataset_dir(dataset_name)
        if not dataset_path.exists():
            raise FileNotFoundError(dataset_name)
        files: list[DatasetFileInfo] = []
        for file in self._iter_audio_files(dataset_path):
            files.append(
                DatasetFileInfo(
                    name=file.name,
                    path=str(file),
                    size_bytes=file.stat().st_size,
                    duration_seconds=self._duration_seconds(file),
                )
            )
        return DatasetDetails(summary=self._summary(dataset_path), files=files)

    def validate_dataset(self, dataset_path: str, min_audio_seconds: float = 0.0, max_audio_seconds: float = 0.0) -> DatasetDetails:
        path = self._resolve_dataset_path(dataset_path)
        if not path.exists():
            raise FileNotFoundError(dataset_path)
        files: list[DatasetFileInfo] = []
        for file in self._iter_audio_files(path):
            duration = self._duration_seconds(file)
            valid = True
            reason = None
            if min_audio_seconds > 0 and duration is not None and duration < min_audio_seconds:
                valid = False
                reason = f"shorter than min_audio_seconds ({min_audio_seconds})"
            if max_audio_seconds > 0 and duration is not None and duration > max_audio_seconds:
                valid = False
                reason = f"longer than max_audio_seconds ({max_audio_seconds})"
            files.append(
                DatasetFileInfo(
                    name=file.name,
                    path=str(file),
                    size_bytes=file.stat().st_size,
                    duration_seconds=duration,
                    valid=valid,
                    reason=reason,
                )
            )
        total_bytes = sum(item.size_bytes for item in files)
        total_seconds = sum(item.duration_seconds or 0.0 for item in files)
        summary = DatasetSummary(
            name=path.name,
            path=str(path),
            file_count=len(files),
            total_bytes=total_bytes,
            total_duration_seconds=round(total_seconds, 4),
            updated_at=utc_now_iso(),
        )
        return DatasetDetails(summary=summary, files=files)

    def save_uploaded_file(self, dataset_name: str, filename: str, payload: bytes) -> DatasetFileInfo:
        if len(payload) > settings.max_upload_bytes:
            raise ValueError(f"payload exceeds max_upload_bytes={settings.max_upload_bytes}")
        dataset_dir = self._safe_dataset_dir(dataset_name)
        dataset_dir.mkdir(parents=True, exist_ok=True)
        safe_file = assert_extension(filename, _AUDIO_EXTENSIONS, "filename")
        target = resolve_inside(dataset_dir, safe_file, "filename")
        target.write_bytes(payload)
        return DatasetFileInfo(
            name=target.name,
            path=str(target),
            size_bytes=target.stat().st_size,
            duration_seconds=self._duration_seconds(target),
        )

    def _preprocess_file(
        self,
        source_path: Path,
        output_dir: Path,
        *,
        silence_trimming: bool,
        normalization: bool,
        auto_segmentation: bool,
        segment_seconds: int,
    ) -> tuple[int, int]:
        base_stem = source_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        existing = list(output_dir.glob(f"{base_stem}_*.wav")) if auto_segmentation else [output_dir / f"{base_stem}.wav"]
        if existing and all(path.exists() for path in existing):
            return (0, len(existing))

        filters: list[str] = []
        if silence_trimming:
            threshold = settings.dataset_silence_threshold_db
            filters.append(
                f"silenceremove=start_periods=1:start_silence=0.2:start_threshold={threshold}dB:"
                f"stop_periods=1:stop_silence=0.2:stop_threshold={threshold}dB"
            )
        if normalization:
            filters.append("loudnorm")
        audio_filter = ",".join(filters) if filters else "anull"

        if auto_segmentation:
            target_pattern = output_dir / f"{base_stem}_%04d.wav"
            command = [
                ffmpeg_binary(),
                "-y",
                "-i",
                str(source_path),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "40000",
                "-af",
                audio_filter,
                "-f",
                "segment",
                "-segment_time",
                str(max(2, segment_seconds)),
                "-reset_timestamps",
                "1",
                str(target_pattern),
            ]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "ffmpeg segmentation failed")
            created = list(output_dir.glob(f"{base_stem}_*.wav"))
            if not created:
                raise RuntimeError(f"ffmpeg segmentation produced no output for {source_path.name}")
            return (len(created), 0)

        target = output_dir / f"{base_stem}.wav"
        command = [
            ffmpeg_binary(),
            "-y",
            "-i",
            str(source_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "40000",
            "-af",
            audio_filter,
            str(target),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "ffmpeg preprocessing failed")
        return (1, 0)

    def prepare_dataset(
        self,
        *,
        dataset_name: str,
        silence_trimming: bool = True,
        normalization: bool = True,
        auto_segmentation: bool = True,
        segment_seconds: int | None = None,
    ) -> DatasetPrepareResponse:
        safe_name = sanitize_name(dataset_name, "dataset_name")
        source_dir = self._safe_dataset_dir(safe_name)
        if not source_dir.exists():
            raise FileNotFoundError(safe_name)
        normalized_segment_seconds = max(2, int(segment_seconds or settings.dataset_segment_seconds))
        prepared_dir = resolve_inside(self.preprocessed_dir, safe_name, "dataset_name")
        prepared_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = prepared_dir / "manifest.json"
        manifest_payload = {
            "silence_trimming": silence_trimming,
            "normalization": normalization,
            "auto_segmentation": auto_segmentation,
            "segment_seconds": normalized_segment_seconds,
        }
        source_files = self._iter_audio_files(source_dir)
        previous_manifest = None
        if manifest_path.exists():
            try:
                previous_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                previous_manifest = None
        processed_files = self._iter_audio_files(prepared_dir)
        if previous_manifest == manifest_payload and processed_files:
            total_seconds = sum(self._duration_seconds(path) or 0.0 for path in processed_files)
            return DatasetPrepareResponse(
                dataset_name=safe_name,
                source_path=str(source_dir),
                prepared_path=str(prepared_dir),
                file_count=len(processed_files),
                created_count=0,
                skipped_count=len(processed_files),
                total_duration_seconds=round(total_seconds, 4),
                reused=True,
            )

        created_count = 0
        skipped_count = 0
        for file in source_files:
            created, skipped = self._preprocess_file(
                file,
                prepared_dir,
                silence_trimming=silence_trimming,
                normalization=normalization,
                auto_segmentation=auto_segmentation,
                segment_seconds=normalized_segment_seconds,
            )
            created_count += created
            skipped_count += skipped
        manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        processed_files = self._iter_audio_files(prepared_dir)
        total_seconds = sum(self._duration_seconds(path) or 0.0 for path in processed_files)
        return DatasetPrepareResponse(
            dataset_name=safe_name,
            source_path=str(source_dir),
            prepared_path=str(prepared_dir),
            file_count=len(processed_files),
            created_count=created_count,
            skipped_count=skipped_count,
            total_duration_seconds=round(total_seconds, 4),
            reused=False,
        )


dataset_service = DatasetService()
