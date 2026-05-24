from __future__ import annotations

from app.backend.core.jsonio import read_json, write_json
from app.backend.core.settings import settings
from app.backend.models.schemas import RuntimeSettings, RuntimeSettingsUpdate


class SettingsService:
    def __init__(self) -> None:
        self.path = settings.runtime_dir / "settings.json"

    def get(self) -> RuntimeSettings:
        if not self.path.exists():
            return RuntimeSettings()
        try:
            return RuntimeSettings.parse_obj(read_json(self.path))
        except Exception:
            return RuntimeSettings()

    def update(self, payload: RuntimeSettingsUpdate) -> RuntimeSettings:
        current = self.get().dict()
        updates = payload.dict(exclude_unset=True)
        current.update(updates)
        merged = RuntimeSettings.parse_obj(current)
        write_json(self.path, merged.dict())
        return merged


settings_service = SettingsService()

