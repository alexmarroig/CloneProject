from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.backend.core.paths import assert_extension
from app.backend.core.settings import settings
from app.backend.models.schemas import ModelInfo


class ModelService:
    def __init__(self) -> None:
        self.weights_dir = settings.rvc_weights_dir
        self.indices_dir = settings.rvc_indices_dir

    def _model_info(self, path: Path, kind: str) -> ModelInfo:
        updated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        return ModelInfo(
            name=path.name,
            path=str(path),
            size_bytes=path.stat().st_size,
            updated_at=updated_at,
            kind=kind,
        )

    def list_models(self) -> list[ModelInfo]:
        models: list[ModelInfo] = []
        for path in sorted(self.weights_dir.glob("*.pth")):
            models.append(self._model_info(path, "weight"))
        for path in sorted(self.indices_dir.glob("*.index")):
            models.append(self._model_info(path, "index"))
        return models

    def delete_model(self, filename: str) -> bool:
        safe = Path(filename).name
        assert_extension(safe, {".pth", ".index"}, "filename")
        candidates = [self.weights_dir / safe, self.indices_dir / safe]
        removed = False
        for item in candidates:
            if item.exists() and item.is_file():
                item.unlink()
                removed = True
        return removed

    def download_model(self, url: str, filename: str | None = None) -> ModelInfo:
        resolved_name = Path(filename or url.split("?")[0]).name
        if not resolved_name:
            raise ValueError("filename could not be resolved")
        ext = Path(assert_extension(resolved_name, {".pth", ".index"}, "filename")).suffix.lower()
        if ext == ".pth":
            target = self.weights_dir / resolved_name
            kind = "weight"
        elif ext == ".index":
            target = self.indices_dir / resolved_name
            kind = "index"
        else:
            raise ValueError("Only .pth or .index downloads are supported")
        with httpx.stream("GET", url, timeout=120.0, follow_redirects=True) as response:
            response.raise_for_status()
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("wb") as file:
                for chunk in response.iter_bytes():
                    file.write(chunk)
        return self._model_info(target, kind)


model_service = ModelService()
