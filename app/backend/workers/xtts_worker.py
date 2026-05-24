from __future__ import annotations

import json
import os
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MAX_CACHE = 2
_TTS_CACHE: OrderedDict[str, object] = OrderedDict()


def _resolve_cached_tts(model_name: str, device: str):
    cache_key = f"{model_name}::{device}"
    cached = _TTS_CACHE.get(cache_key)
    if cached is not None:
        _TTS_CACHE.move_to_end(cache_key, last=True)
        return cached
    try:
        from TTS.api import TTS
    except Exception as exc:
        raise RuntimeError(
            "XTTS dependencies are not installed in app/runtime/envs/xtts. Install Coqui TTS in that environment first."
        ) from exc
    model = TTS(model_name=model_name).to(device)
    _TTS_CACHE[cache_key] = model
    _TTS_CACHE.move_to_end(cache_key, last=True)
    while len(_TTS_CACHE) > MAX_CACHE:
        _TTS_CACHE.popitem(last=False)
    return model


def main() -> None:
    payload = json.loads(sys.argv[1])
    output_path = Path(payload["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    speaker_wav = payload.get("speaker_wav") or os.getenv("VOICE_ENGINE_XTTS_SPEAKER_WAV")
    if not speaker_wav:
        default_speaker = Path(payload["models_dir"]) / "speaker.wav"
        if default_speaker.exists():
            speaker_wav = str(default_speaker)

    if not speaker_wav:
        raise RuntimeError(
            "XTTS requires a reference speaker wav. Set VOICE_ENGINE_XTTS_SPEAKER_WAV or place speaker.wav in app/models/xtts/."
        )

    device = payload.get("device", "cpu")
    model_name = payload.get("model") or os.getenv("VOICE_ENGINE_XTTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2")
    tts = _resolve_cached_tts(model_name=model_name, device=device)
    generation_kwargs = {
        "text": payload["text"],
        "file_path": str(output_path),
        "speaker_wav": speaker_wav,
        "language": payload["language"],
        "speed": payload.get("speed", 1.0),
        "temperature": payload.get("temperature", 0.7),
        "top_k": payload.get("top_k", 50),
        "top_p": payload.get("top_p", 0.8),
        "repetition_penalty": payload.get("repetition_penalty", 2.0),
    }
    if payload.get("emotion"):
        generation_kwargs["emotion"] = payload["emotion"]
    try:
        tts.tts_to_file(**generation_kwargs)
    except TypeError:
        # Older TTS versions do not support all generation kwargs.
        tts.tts_to_file(
            text=payload["text"],
            file_path=str(output_path),
            speaker_wav=speaker_wav,
            language=payload["language"],
            speed=payload.get("speed", 1.0),
        )
    print(json.dumps({"output_path": str(output_path)}))


if __name__ == "__main__":
    main()
