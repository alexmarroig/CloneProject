from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from app.backend.models.schemas import VoiceMetadata


class VoiceRegistry:
    def __init__(self, voices_dir: Path):
        self.voices_dir = voices_dir

    def list_voices(self) -> list[VoiceMetadata]:
        voices: list[VoiceMetadata] = []
        for metadata_path in sorted(self.voices_dir.glob("*/voice.json")):
            try:
                voices.append(VoiceMetadata.parse_raw(metadata_path.read_text(encoding="utf-8")))
            except Exception:
                continue
        return voices

    def get_voice(self, voice_name: str) -> VoiceMetadata | None:
        metadata_path = self.voices_dir / voice_name / "voice.json"
        if not metadata_path.exists():
            return None
        return VoiceMetadata.parse_raw(metadata_path.read_text(encoding="utf-8"))

    def save_voice(self, metadata: VoiceMetadata) -> None:
        voice_dir = self.voices_dir / metadata.name
        voice_dir.mkdir(parents=True, exist_ok=True)
        (voice_dir / "voice.json").write_text(metadata.json(indent=2), encoding="utf-8")


class VoiceCache:
    def __init__(self, max_items: int):
        self.max_items = max_items
        self._items: OrderedDict[str, VoiceMetadata] = OrderedDict()

    def get(self, name: str) -> VoiceMetadata | None:
        item = self._items.get(name)
        if item:
            self._items.move_to_end(name)
        return item

    def put(self, metadata: VoiceMetadata) -> None:
        self._items[metadata.name] = metadata
        self._items.move_to_end(metadata.name)
        while len(self._items) > self.max_items:
            self._items.popitem(last=False)
