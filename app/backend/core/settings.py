from __future__ import annotations

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {
        "env_prefix": "VOICE_ENGINE_",
        "env_file": ".env",
        "extra": "ignore",
    }

    app_name: str = "Voice Engine API"
    base_dir: Path = Path(__file__).resolve().parents[3]
    app_dir: Path = base_dir / "app"
    runtime_dir: Path = app_dir / "runtime"
    runtime_logs_dir: Path = runtime_dir / "logs"
    jobs_dir: Path = runtime_dir / "jobs"
    jobs_db_path: Path = runtime_dir / "jobs.sqlite3"
    datasets_dir: Path = runtime_dir / "datasets"
    datasets_preprocessed_dir: Path = runtime_dir / "datasets_preprocessed"
    audio_input_dir: Path = runtime_dir / "audio" / "input"
    audio_intermediate_dir: Path = runtime_dir / "audio" / "intermediate"
    audio_output_dir: Path = runtime_dir / "audio" / "output"
    models_dir: Path = app_dir / "models"
    voices_dir: Path = models_dir / "voices"
    xtts_models_dir: Path = models_dir / "xtts"
    xtts_env_python: Path = runtime_dir / "envs" / "xtts" / "Scripts" / "python.exe"
    rvc_env_python: Path = runtime_dir / "envs" / "rvc" / "Scripts" / "python.exe"
    xtts_worker_script: Path = app_dir / "backend" / "workers" / "xtts_worker.py"
    rvc_worker_script: Path = app_dir / "backend" / "workers" / "rvc_worker.py"
    rvc_root_dir: Path = base_dir
    rvc_weights_dir: Path = base_dir / "assets" / "weights"
    rvc_indices_dir: Path = base_dir / "assets" / "indices"
    worker_pool_size: int = 2
    default_device: str = Field(default="auto")
    gpu_device: str = Field(default="0", env=["GPU_DEVICE", "VOICE_ENGINE_GPU_DEVICE"])
    ffmpeg_path: Path = base_dir / "ffmpeg.exe"
    ffprobe_path: Path = base_dir / "ffprobe.exe"
    job_poll_interval_seconds: float = 0.5
    generate_timeout_min_seconds: int = 120
    generate_timeout_factor: float = 5.0
    event_stream_poll_seconds: float = 0.75
    event_stream_keepalive_seconds: int = 25
    train_timeout_seconds: int = 7200
    max_loaded_voices: int = 3
    max_upload_bytes: int = 50 * 1024 * 1024
    allowed_audio_extensions: tuple[str, ...] = (".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac")
    dataset_segment_seconds: int = 12
    dataset_silence_threshold_db: int = -45


settings = Settings()

for directory in [
    settings.runtime_logs_dir,
    settings.jobs_dir,
    settings.datasets_dir,
    settings.datasets_preprocessed_dir,
    settings.audio_input_dir,
    settings.audio_intermediate_dir,
    settings.audio_output_dir,
    settings.voices_dir,
    settings.xtts_models_dir,
    settings.rvc_weights_dir,
    settings.rvc_indices_dir,
]:
    directory.mkdir(parents=True, exist_ok=True)
