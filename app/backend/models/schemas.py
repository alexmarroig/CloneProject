from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobType(str, Enum):
    GENERATE = "generate_voice"
    TRAIN = "train_voice"
    CONVERT = "convert_voice"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GeneratePhase(str, Enum):
    QUEUED = "queued"
    XTTS_GENERATION = "xtts_generation"
    RVC_CONVERSION = "rvc_conversion"
    FINALIZING = "finalizing"
    COMPLETED = "completed"


class TrainPhase(str, Enum):
    QUEUED = "queued"
    PREPROCESS = "preprocess"
    EXTRACT_PITCH = "extract_pitch"
    EXTRACT_FEATURES = "extract_features"
    TRAINING = "training"
    INDEXING = "indexing"
    COMPLETED = "completed"


class GenerateVoiceRequest(BaseModel):
    text: str = Field(min_length=1)
    voice: str = Field(min_length=1)
    language: str = Field(min_length=2, max_length=8)
    model: str | None = None
    emotion: str | None = None
    speed: float = 1.0
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 0.8
    repetition_penalty: float = 2.0
    speaker_wav: str | None = None
    gpu_device: str = "auto"
    use_gpu: bool = True
    pitch_shift: int = 0
    index_rate: float = 0.66
    f0_method: str = "rmvpe"
    filter_radius: int = 3
    resample_rate: int = 0
    rms_mix_rate: float = 1.0
    protect_consonants: float = 0.33
    normalize: bool = True


class TrainVoiceRequest(BaseModel):
    voice_name: str = Field(min_length=1)
    dataset_path: str = Field(min_length=1)
    dataset_name: str | None = None
    base_model: str | None = None
    silence_slicing: bool = True
    normalize: bool = True
    min_audio_seconds: float = 0.0
    max_audio_seconds: float = 0.0
    segment_seconds: int = 12
    sample_rate: str = "40k"
    f0_method: str = "rmvpe"
    epochs: int = 300
    batch_size: int = 1
    learning_rate: float = 0.0001
    save_every_epoch: int = 10
    gpu_device: str = "auto"
    mixed_precision: bool = False
    version: str = "v2"
    use_gpu: bool = True


class ConvertVoiceRequest(BaseModel):
    input_path: str = Field(min_length=1)
    voice: str | None = None
    model_path: str | None = None
    index_path: str | None = None
    pitch_shift: int = 0
    index_rate: float = 0.66
    f0_method: str = "rmvpe"
    filter_radius: int = 3
    resample_rate: int = 0
    rms_mix_rate: float = 1.0
    protect_consonants: float = 0.33
    gpu_device: str = "auto"
    use_gpu: bool = True


class DatasetValidateRequest(BaseModel):
    dataset_path: str = Field(min_length=1)
    min_audio_seconds: float = 0.0
    max_audio_seconds: float = 0.0


class DatasetPrepareRequest(BaseModel):
    dataset_name: str = Field(min_length=1)
    silence_trimming: bool = True
    normalization: bool = True
    auto_segmentation: bool = True
    segment_seconds: int = 12


class DatasetPrepareResponse(BaseModel):
    dataset_name: str
    source_path: str
    prepared_path: str
    file_count: int
    created_count: int
    skipped_count: int
    total_duration_seconds: float
    reused: bool


class ModelDownloadRequest(BaseModel):
    url: str = Field(min_length=8)
    filename: str | None = None


class JobArtifact(BaseModel):
    type: str
    path: str


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobState(BaseModel):
    id: str
    type: JobType
    status: JobStatus
    phase: str
    progress: int = 0
    payload: dict[str, Any]
    error: str | None = None
    artifacts: list[JobArtifact] = Field(default_factory=list)
    created_at: str
    updated_at: str
    started_at: str | None = None
    finished_at: str | None = None


class VoiceMetadata(BaseModel):
    name: str
    display_name: str
    model_path: str
    index_path: str
    dataset_path: str | None = None
    base_model: str | None = None
    languages: list[str] = Field(default_factory=list)
    sample_rate: int
    status: str
    created_at: str
    updated_at: str
    rvc_version: str


class VoicesResponse(BaseModel):
    voices: list[VoiceMetadata]


class HealthResponse(BaseModel):
    status: str
    device: str
    ffmpeg_available: bool
    xtts_env_available: bool
    rvc_env_available: bool
    voices_count: int


class DatasetFileInfo(BaseModel):
    name: str
    path: str
    size_bytes: int
    duration_seconds: float | None = None
    valid: bool = True
    reason: str | None = None


class DatasetSummary(BaseModel):
    name: str
    path: str
    file_count: int
    total_bytes: int
    total_duration_seconds: float
    updated_at: str


class DatasetsResponse(BaseModel):
    datasets: list[DatasetSummary]


class DatasetDetails(BaseModel):
    summary: DatasetSummary
    files: list[DatasetFileInfo]


class ModelInfo(BaseModel):
    name: str
    path: str
    size_bytes: int
    updated_at: str
    kind: str


class ModelsResponse(BaseModel):
    models: list[ModelInfo]


class TrainingMetricPoint(BaseModel):
    step: int
    loss_disc: float | None = None
    loss_gen: float | None = None
    loss_fm: float | None = None
    loss_mel: float | None = None
    loss_kl: float | None = None


class GpuUsage(BaseModel):
    gpu_name: str | None = None
    utilization_percent: float | None = None
    memory_used_mb: float | None = None
    memory_total_mb: float | None = None


class JobEvent(BaseModel):
    id: int
    job_id: str
    level: str
    message: str
    created_at: str
    data: dict[str, Any] | None = None


class JobLogsResponse(BaseModel):
    job_id: str
    voice_name: str | None = None
    logs: dict[str, str]
    metrics: list[TrainingMetricPoint]
    gpu: GpuUsage | None = None
    events: list[JobEvent] = Field(default_factory=list)


class JobEventsResponse(BaseModel):
    job_id: str
    since_id: int
    events: list[JobEvent] = Field(default_factory=list)


class RuntimeSettings(BaseModel):
    default_xtts_model: str | None = None
    default_rvc_model: str | None = None


class RuntimeSettingsUpdate(BaseModel):
    default_xtts_model: str | None = None
    default_rvc_model: str | None = None
