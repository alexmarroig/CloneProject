from __future__ import annotations

from math import ceil
from pathlib import Path
import shutil

from app.backend.core.settings import settings
from app.backend.core.timeutils import utc_now_iso
from app.backend.models.schemas import JobArtifact, VoiceMetadata
from app.backend.services.audio_processing import final_master, normalize_resample, probe_duration
from app.backend.services.dataset_service import dataset_service
from app.backend.services.job_manager import job_manager
from app.backend.services.rvc_service import rvc_service
from app.backend.services.voice_registry import VoiceRegistry
from app.backend.services.xtts_service import xtts_service


registry = VoiceRegistry(settings.voices_dir)
_SAMPLE_RATE_MAP = {"32k": 32000, "40k": 40000, "48k": 48000}


class PipelineService:
    def _timeout_from_duration(self, duration_seconds: float | None) -> int:
        if duration_seconds is None:
            return settings.generate_timeout_min_seconds
        return max(
            settings.generate_timeout_min_seconds,
            int(ceil(max(1.0, duration_seconds) * settings.generate_timeout_factor)),
        )

    def _estimate_tts_duration(self, text: str) -> float:
        # 15 chars/s gives a conservative speech-time estimate for timeout budgeting.
        return max(8.0, len(text) / 15.0)

    def run_generate(self, job_id: str, payload: dict) -> list[JobArtifact]:
        voice = registry.get_voice(payload["voice"])
        if voice is None:
            raise RuntimeError(f"Voice '{payload['voice']}' not found")

        base_audio = settings.audio_intermediate_dir / f"{job_id}_xtts.wav"
        normalized_audio = settings.audio_intermediate_dir / f"{job_id}_normalized.wav"
        rvc_audio = settings.audio_intermediate_dir / f"{job_id}_rvc.wav"
        final_audio = settings.audio_output_dir / f"{job_id}.wav"

        job_manager.update(job_id, phase="xtts_generation", progress=20)
        xtts_timeout = self._timeout_from_duration(self._estimate_tts_duration(payload.get("text", "")))
        job_manager.record_event(job_id, "Starting XTTS generation", data={"timeout_seconds": xtts_timeout})
        xtts_service.generate_base_audio(
            text=payload["text"],
            language=payload["language"],
            output_path=base_audio,
            model=payload.get("model"),
            emotion=payload.get("emotion"),
            speed=payload.get("speed", 1.0),
            temperature=payload.get("temperature", 0.7),
            top_k=payload.get("top_k", 50),
            top_p=payload.get("top_p", 0.8),
            repetition_penalty=payload.get("repetition_penalty", 2.0),
            speaker_wav=payload.get("speaker_wav"),
            use_gpu=payload.get("use_gpu", True),
            gpu_device=payload.get("gpu_device", "auto"),
            timeout=xtts_timeout,
        )

        if payload.get("normalize", True):
            normalize_resample(base_audio, normalized_audio, 16000)
        else:
            shutil.copy2(base_audio, normalized_audio)

        job_manager.update(job_id, phase="rvc_conversion", progress=65)
        try:
            normalized_duration = probe_duration(normalized_audio)
        except Exception:
            normalized_duration = None
        convert_timeout = self._timeout_from_duration(normalized_duration)
        job_manager.record_event(
            job_id,
            "Starting RVC conversion",
            data={
                "audio_seconds": round(normalized_duration, 3) if normalized_duration is not None else None,
                "timeout_seconds": convert_timeout,
            },
        )
        rvc_service.convert_voice(
            input_path=normalized_audio,
            output_path=rvc_audio,
            model_path=Path(voice.model_path),
            index_path=Path(voice.index_path),
            pitch_shift=payload.get("pitch_shift", 0),
            index_rate=payload.get("index_rate", 0.66),
            f0_method=payload.get("f0_method", "rmvpe"),
            filter_radius=payload.get("filter_radius", 3),
            resample_rate=payload.get("resample_rate", 0),
            rms_mix_rate=payload.get("rms_mix_rate", 1.0),
            protect_consonants=payload.get("protect_consonants", 0.33),
            gpu_device=payload.get("gpu_device", "auto"),
            use_gpu=payload.get("use_gpu", True),
            timeout=convert_timeout,
        )

        job_manager.update(job_id, phase="finalizing", progress=90)
        final_master(rvc_audio, final_audio, voice.sample_rate)
        return [JobArtifact(type="audio/wav", path=str(final_audio))]

    def run_convert(self, job_id: str, payload: dict) -> list[JobArtifact]:
        model_path = payload.get("model_path")
        index_path = payload.get("index_path")
        sample_rate = 40000
        if payload.get("voice"):
            voice = registry.get_voice(payload["voice"])
            if voice is None:
                raise RuntimeError(f"Voice '{payload['voice']}' not found")
            model_path = voice.model_path
            index_path = voice.index_path
            sample_rate = voice.sample_rate
        if not model_path or not index_path:
            raise RuntimeError("model_path and index_path are required")
        input_path = Path(payload["input_path"])
        if not input_path.exists():
            raise RuntimeError(f"Input audio not found: {input_path}")

        converted_path = settings.audio_intermediate_dir / f"{job_id}_convert.wav"
        output_path = settings.audio_output_dir / f"{job_id}_convert_master.wav"
        try:
            source_duration = probe_duration(input_path)
        except Exception:
            source_duration = None
        convert_timeout = self._timeout_from_duration(source_duration)
        job_manager.record_event(
            job_id,
            "Starting direct conversion",
            data={
                "audio_seconds": round(source_duration, 3) if source_duration is not None else None,
                "timeout_seconds": convert_timeout,
            },
        )
        job_manager.update(job_id, phase="rvc_conversion", progress=60)
        rvc_service.convert_voice(
            input_path=input_path,
            output_path=converted_path,
            model_path=Path(model_path),
            index_path=Path(index_path),
            pitch_shift=payload.get("pitch_shift", 0),
            index_rate=payload.get("index_rate", 0.66),
            f0_method=payload.get("f0_method", "rmvpe"),
            filter_radius=payload.get("filter_radius", 3),
            resample_rate=payload.get("resample_rate", 0),
            rms_mix_rate=payload.get("rms_mix_rate", 1.0),
            protect_consonants=payload.get("protect_consonants", 0.33),
            gpu_device=payload.get("gpu_device", "auto"),
            use_gpu=payload.get("use_gpu", True),
            timeout=convert_timeout,
        )
        final_master(converted_path, output_path, sample_rate)
        return [JobArtifact(type="audio/wav", path=str(output_path))]

    def run_train(self, job_id: str, payload: dict) -> list[JobArtifact]:
        voice_name = payload["voice_name"]
        sample_rate = payload.get("sample_rate", "40k")
        version = payload.get("version", "v2")
        dataset_name = payload.get("dataset_name")
        dataset_path = payload.get("dataset_path")

        if dataset_name:
            job_manager.update(job_id, phase="dataset_preprocess", progress=5)
            prepared = dataset_service.prepare_dataset(
                dataset_name=dataset_name,
                silence_trimming=payload.get("silence_slicing", True),
                normalization=payload.get("normalize", True),
                auto_segmentation=True,
                segment_seconds=payload.get("segment_seconds"),
            )
            dataset_path = prepared.prepared_path
            payload["dataset_path"] = dataset_path
            job_manager.record_event(
                job_id,
                "Dataset preprocessing finished",
                data={
                    "dataset_name": dataset_name,
                    "prepared_path": prepared.prepared_path,
                    "created_count": prepared.created_count,
                    "skipped_count": prepared.skipped_count,
                    "reused": prepared.reused,
                },
            )

        job_manager.update(job_id, phase="preprocess", progress=10)
        rvc_service.preprocess(
            voice_name=voice_name,
            dataset_path=str(dataset_path),
            sample_rate=sample_rate,
            silence_slicing=payload.get("silence_slicing", True),
            normalize=payload.get("normalize", True),
            min_audio_seconds=payload.get("min_audio_seconds", 0.0),
            max_audio_seconds=payload.get("max_audio_seconds", 0.0),
            timeout=min(settings.train_timeout_seconds, 1800),
        )

        job_manager.update(job_id, phase="extract_pitch", progress=25)
        rvc_service.extract_pitch(
            voice_name=voice_name,
            f0_method=payload.get("f0_method", "rmvpe"),
            timeout=min(settings.train_timeout_seconds, 1800),
        )

        job_manager.update(job_id, phase="extract_features", progress=45)
        rvc_service.extract_features(
            voice_name=voice_name,
            version=version,
            use_gpu=payload.get("use_gpu", True),
            gpu_device=payload.get("gpu_device", "auto"),
            timeout=min(settings.train_timeout_seconds, 1800),
        )

        job_manager.update(job_id, phase="training", progress=70)
        train_result = rvc_service.train(
            voice_name=voice_name,
            sample_rate=sample_rate,
            epochs=payload.get("epochs", 300),
            batch_size=payload.get("batch_size", 1),
            learning_rate=payload.get("learning_rate", 0.0001),
            save_every_epoch=payload.get("save_every_epoch", 10),
            mixed_precision=payload.get("mixed_precision", False),
            version=version,
            use_gpu=payload.get("use_gpu", True),
            gpu_device=payload.get("gpu_device", "auto"),
            timeout=settings.train_timeout_seconds,
        )

        job_manager.update(job_id, phase="indexing", progress=90)
        index_result = rvc_service.build_index(
            voice_name=voice_name,
            version=version,
            timeout=min(settings.train_timeout_seconds, 1800),
        )

        metadata = VoiceMetadata(
            name=voice_name,
            display_name=voice_name,
            model_path=train_result["model_path"],
            index_path=index_result["index_path"],
            dataset_path=payload.get("dataset_path"),
            base_model=payload.get("base_model"),
            languages=[],
            sample_rate=_SAMPLE_RATE_MAP.get(sample_rate, 40000),
            status="ready",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
            rvc_version=version,
        )
        registry.save_voice(metadata)
        return [
            JobArtifact(type="model/pth", path=metadata.model_path),
            JobArtifact(type="model/index", path=metadata.index_path),
        ]


pipeline_service = PipelineService()
