from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
import re

from app.backend.core.settings import settings


def resolve_python(executable: Path) -> str:
    if executable.exists():
        return str(executable)
    return "python"


def _normalize_device_name(value: str | None) -> str:
    if not value:
        return "auto"
    lowered = value.strip().lower()
    if lowered in {"", "auto"}:
        return "auto"
    if lowered in {"cpu", "mps"}:
        return lowered
    if lowered.startswith("cuda") or lowered.isdigit():
        return "cuda"
    return "auto"


def _normalize_gpu_index(value: str | None) -> str:
    raw = (value or settings.gpu_device or "0").strip().lower()
    if raw.startswith("cuda:"):
        raw = raw.split(":", 1)[1]
    if raw.startswith("gpu:"):
        raw = raw.split(":", 1)[1]
    match = re.search(r"\d+", raw)
    if not match:
        return "0"
    return match.group(0)


def resolve_device(
    use_gpu: bool = True,
    requested_device: str | None = None,
    requested_gpu_index: str | None = None,
) -> tuple[str, str | None]:
    if not use_gpu:
        return "cpu", None

    explicit = _normalize_device_name(requested_device)
    if explicit == "auto" and settings.default_device and settings.default_device.lower() != "auto":
        explicit = _normalize_device_name(settings.default_device)

    try:
        import torch
    except Exception:
        torch = None  # type: ignore[assignment]

    if explicit == "cpu":
        return "cpu", None

    if explicit == "mps":
        if torch is not None and getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps", None
        return "cpu", None

    if torch is not None and torch.cuda.is_available():
        preferred_gpu = requested_gpu_index
        if not preferred_gpu and requested_device:
            preferred_gpu = requested_device
        return "cuda", _normalize_gpu_index(preferred_gpu)

    if explicit == "auto" and torch is not None and getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps", None

    return "cpu", None


def format_device_for_framework(device: str, gpu_index: str | None) -> str:
    if device != "cuda":
        return device
    if gpu_index is None:
        return "cuda"
    return f"cuda:{gpu_index}"


def ffmpeg_binary() -> str:
    if settings.ffmpeg_path.exists():
        return str(settings.ffmpeg_path)
    found = shutil.which("ffmpeg")
    return found or "ffmpeg"


def ffprobe_binary() -> str:
    if settings.ffprobe_path.exists():
        return str(settings.ffprobe_path)
    found = shutil.which("ffprobe")
    return found or "ffprobe"


def run_command(command: list[str], cwd: Path | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
