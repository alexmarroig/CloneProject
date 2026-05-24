from __future__ import annotations

import subprocess
from pathlib import Path

from app.backend.core.runtime import ffmpeg_binary, ffprobe_binary


def normalize_resample(input_path: Path, output_path: Path, sample_rate: int = 16000) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_binary(),
        "-y",
        "-i",
        str(input_path),
        "-af",
        "loudnorm",
        "-ar",
        str(sample_rate),
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return output_path


def final_master(input_path: Path, output_path: Path, sample_rate: int = 24000) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_binary(),
        "-y",
        "-i",
        str(input_path),
        "-af",
        "loudnorm,atrim=start=0",
        "-ar",
        str(sample_rate),
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return output_path


def probe_duration(input_path: Path) -> float:
    cmd = [
        ffprobe_binary(),
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(input_path),
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(completed.stdout.strip())
