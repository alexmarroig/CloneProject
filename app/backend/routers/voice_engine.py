from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import Iterable

from fastapi import APIRouter, Body, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse

from app.backend.core.paths import assert_extension, resolve_inside, sanitize_name
from app.backend.core.settings import settings
from app.backend.models.schemas import (
    ConvertVoiceRequest,
    DatasetPrepareRequest,
    DatasetValidateRequest,
    DatasetsResponse,
    GenerateVoiceRequest,
    HealthResponse,
    JobEventsResponse,
    JobLogsResponse,
    JobResponse,
    JobType,
    ModelDownloadRequest,
    ModelsResponse,
    RuntimeSettings,
    RuntimeSettingsUpdate,
    TrainVoiceRequest,
    VoicesResponse,
)
from app.backend.services.dataset_service import dataset_service
from app.backend.services.job_manager import job_manager
from app.backend.services.log_service import log_service
from app.backend.services.model_service import model_service
from app.backend.services.pipeline_service import pipeline_service
from app.backend.services.settings_service import settings_service
from app.backend.services.voice_registry import VoiceRegistry

router = APIRouter()
registry = VoiceRegistry(settings.voices_dir)


def _resolve_allowed_path(candidate: str, roots: Iterable[Path], field: str, *, must_exist: bool = True) -> Path:
    for root in roots:
        try:
            return resolve_inside(root, candidate, field, must_exist=must_exist)
        except Exception:
            continue
    raise ValueError(f"{field} must resolve inside allowed runtime directories")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        device=settings.default_device,
        ffmpeg_available=settings.ffmpeg_path.exists(),
        xtts_env_available=settings.xtts_env_python.exists(),
        rvc_env_available=settings.rvc_env_python.exists(),
        voices_count=len(registry.list_voices()),
    )


@router.get("/voices", response_model=VoicesResponse)
def list_voices() -> VoicesResponse:
    return VoicesResponse(voices=registry.list_voices())


@router.post("/generate_voice", response_model=JobResponse)
def generate_voice(payload: GenerateVoiceRequest) -> JobResponse:
    try:
        safe_voice = sanitize_name(payload.voice, "voice")
        if registry.get_voice(safe_voice) is None:
            raise HTTPException(status_code=404, detail=f"Voice '{safe_voice}' not found")
        request_payload = payload.dict()
        request_payload["voice"] = safe_voice
        job = job_manager.create_job(JobType.GENERATE, request_payload)
        job_manager.enqueue(job, pipeline_service.run_generate)
        return JobResponse(job_id=job.id, status=job.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/train_voice", response_model=JobResponse)
def train_voice(payload: TrainVoiceRequest) -> JobResponse:
    try:
        safe_voice_name = sanitize_name(payload.voice_name, "voice_name")
        safe_dataset_name = sanitize_name(payload.dataset_name, "dataset_name") if payload.dataset_name else None
        train_payload = payload.dict()
        train_payload["voice_name"] = safe_voice_name
        train_payload["dataset_name"] = safe_dataset_name
        if safe_dataset_name and payload.dataset_path == ".":
            train_payload["dataset_path"] = str(resolve_inside(settings.datasets_dir, safe_dataset_name, "dataset_name"))
        dataset_path = _resolve_allowed_path(
            train_payload["dataset_path"],
            (settings.datasets_dir, settings.datasets_preprocessed_dir),
            "dataset_path",
            must_exist=True,
        )
        train_payload["dataset_path"] = str(dataset_path)
        if payload.gpu_device in {"cpu", "cuda", "mps"}:
            train_payload["use_gpu"] = payload.gpu_device != "cpu"
        job = job_manager.create_job(JobType.TRAIN, train_payload)
        job_manager.enqueue(job, pipeline_service.run_train)
        return JobResponse(job_id=job.id, status=job.status)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/convert_voice", response_model=JobResponse)
def convert_voice(payload: ConvertVoiceRequest) -> JobResponse:
    convert_payload = payload.dict()
    try:
        if payload.voice:
            safe_voice = sanitize_name(payload.voice, "voice")
            if registry.get_voice(safe_voice) is None:
                raise HTTPException(status_code=404, detail=f"Voice '{safe_voice}' not found")
            convert_payload["voice"] = safe_voice
        input_path = _resolve_allowed_path(
            payload.input_path,
            (settings.audio_input_dir, settings.audio_intermediate_dir, settings.audio_output_dir),
            "input_path",
            must_exist=True,
        )
        convert_payload["input_path"] = str(input_path)
        if payload.model_path:
            convert_payload["model_path"] = str(
                _resolve_allowed_path(
                    payload.model_path,
                    (settings.voices_dir, settings.rvc_weights_dir),
                    "model_path",
                    must_exist=True,
                )
            )
        if payload.index_path:
            convert_payload["index_path"] = str(
                _resolve_allowed_path(
                    payload.index_path,
                    (settings.voices_dir, settings.rvc_indices_dir),
                    "index_path",
                    must_exist=True,
                )
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    job = job_manager.create_job(JobType.CONVERT, convert_payload)
    job_manager.enqueue(job, pipeline_service.run_convert)
    return JobResponse(job_id=job.id, status=job.status)


@router.get("/jobs")
def list_jobs() -> dict:
    return {"jobs": [job.dict() for job in job_manager.list_recent()]}


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.dict()


@router.get("/jobs/{job_id}/logs", response_model=JobLogsResponse)
def get_job_logs(job_id: str) -> JobLogsResponse:
    try:
        return log_service.job_logs(job_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")


@router.get("/jobs/{job_id}/events", response_model=JobEventsResponse)
def get_job_events(job_id: str, since_id: int = Query(0, ge=0), limit: int = Query(200, ge=1, le=1000)) -> JobEventsResponse:
    if job_manager.get_job(job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")
    events = job_manager.list_events(job_id, since_id=since_id, limit=limit)
    return JobEventsResponse(job_id=job_id, since_id=since_id, events=events)


@router.get("/jobs/{job_id}/stream")
async def stream_job_events(job_id: str, request: Request) -> StreamingResponse:
    if job_manager.get_job(job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        last_id = 0
        idle_ticks = 0
        while True:
            if await request.is_disconnected():
                break
            events = job_manager.list_events(job_id, since_id=last_id, limit=200)
            if events:
                idle_ticks = 0
                for event in events:
                    last_id = event.id
                    chunk = json.dumps(event.dict(), ensure_ascii=False)
                    yield f"event: job_event\ndata: {chunk}\n\n"
            else:
                idle_ticks += 1
                if idle_ticks * settings.event_stream_poll_seconds >= settings.event_stream_keepalive_seconds:
                    idle_ticks = 0
                    yield ": keepalive\n\n"
            state = job_manager.get_job(job_id)
            if state is None:
                break
            if state.status.value in {"completed", "failed"}:
                done_chunk = json.dumps({"status": state.status.value, "job_id": job_id}, ensure_ascii=False)
                yield f"event: job_done\ndata: {done_chunk}\n\n"
                break
            await asyncio.sleep(settings.event_stream_poll_seconds)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/datasets", response_model=DatasetsResponse)
def list_datasets() -> DatasetsResponse:
    return DatasetsResponse(datasets=dataset_service.list_datasets())


@router.get("/datasets/{dataset_name}")
def dataset_details(dataset_name: str) -> dict:
    try:
        return dataset_service.dataset_details(dataset_name).dict()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/datasets/validate")
def validate_dataset(payload: DatasetValidateRequest) -> dict:
    try:
        return dataset_service.validate_dataset(
            dataset_path=payload.dataset_path,
            min_audio_seconds=payload.min_audio_seconds,
            max_audio_seconds=payload.max_audio_seconds,
        ).dict()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset path not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/datasets/prepare")
def prepare_dataset(payload: DatasetPrepareRequest) -> dict:
    try:
        return dataset_service.prepare_dataset(
            dataset_name=payload.dataset_name,
            silence_trimming=payload.silence_trimming,
            normalization=payload.normalization,
            auto_segmentation=payload.auto_segmentation,
            segment_seconds=payload.segment_seconds,
        ).dict()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/datasets/upload")
def upload_dataset_file(
    request: Request,
    dataset_name: str = Query(..., min_length=1),
    filename: str = Query(..., min_length=1),
    content: bytes = Body(..., media_type="application/octet-stream"),
) -> dict:
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"Upload exceeds max_upload_bytes={settings.max_upload_bytes}")
    try:
        assert_extension(filename, set(settings.allowed_audio_extensions), "filename")
        content_type = request.headers.get("content-type", "").lower()
        allowed_types = (
            "application/octet-stream",
            "audio/wav",
            "audio/x-wav",
            "audio/mpeg",
            "audio/flac",
            "audio/ogg",
            "audio/aac",
            "audio/mp4",
        )
        if content_type and not any(content_type.startswith(item) for item in allowed_types):
            raise ValueError(f"Unsupported content-type: {content_type}")
        file_info = dataset_service.save_uploaded_file(dataset_name=dataset_name, filename=filename, payload=content)
        return file_info.dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/audio/upload")
def upload_audio_input(
    request: Request,
    filename: str = Query(..., min_length=1),
    content: bytes = Body(..., media_type="application/octet-stream"),
) -> dict:
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"Upload exceeds max_upload_bytes={settings.max_upload_bytes}")
    try:
        safe_name = assert_extension(filename, set(settings.allowed_audio_extensions), "filename")
        content_type = request.headers.get("content-type", "").lower()
        allowed_types = (
            "application/octet-stream",
            "audio/wav",
            "audio/x-wav",
            "audio/mpeg",
            "audio/flac",
            "audio/ogg",
            "audio/aac",
            "audio/mp4",
        )
        if content_type and not any(content_type.startswith(item) for item in allowed_types):
            raise ValueError(f"Unsupported content-type: {content_type}")
        target = resolve_inside(settings.audio_input_dir, safe_name, "filename")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    target.write_bytes(content)
    return {"path": str(target), "size_bytes": target.stat().st_size}


@router.get("/models", response_model=ModelsResponse)
def list_models() -> ModelsResponse:
    return ModelsResponse(models=model_service.list_models())


@router.post("/models/download")
def download_model(payload: ModelDownloadRequest) -> dict:
    try:
        return model_service.download_model(url=payload.url, filename=payload.filename).dict()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/models/{filename}")
def delete_model(filename: str) -> dict:
    try:
        removed = model_service.delete_model(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not removed:
        raise HTTPException(status_code=404, detail="Model file not found")
    return {"deleted": True}


@router.delete("/voices/{voice_name}")
def delete_voice(voice_name: str) -> dict:
    try:
        safe_name = sanitize_name(voice_name, "voice_name")
        voice_dir = resolve_inside(settings.voices_dir, safe_name, "voice_name")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not voice_dir.exists():
        raise HTTPException(status_code=404, detail="Voice not found")
    shutil.rmtree(voice_dir)
    return {"deleted": True}


@router.get("/voices/{voice_name}/download/{artifact}")
def download_voice_artifact(voice_name: str, artifact: str) -> FileResponse:
    try:
        safe_name = sanitize_name(voice_name, "voice_name")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    voice = registry.get_voice(safe_name)
    if voice is None:
        raise HTTPException(status_code=404, detail="Voice not found")
    if artifact == "model":
        path = Path(voice.model_path)
    elif artifact == "index":
        path = Path(voice.index_path)
    else:
        raise HTTPException(status_code=400, detail="artifact must be model or index")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact file not found")
    return FileResponse(path=str(path), filename=path.name)


@router.get("/settings", response_model=RuntimeSettings)
def get_runtime_settings() -> RuntimeSettings:
    return settings_service.get()


@router.post("/settings", response_model=RuntimeSettings)
def update_runtime_settings(payload: RuntimeSettingsUpdate) -> RuntimeSettings:
    return settings_service.update(payload)
