from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

import httpx

from app.backend.core.settings import settings
from app.backend.services.settings_service import settings_service


class XTTSService:
    """XTTS service that uses the Docker XTTS server via HTTP API"""

    XTTS_SERVER_URL = "http://localhost:8001"
    MAX_RETRIES = 5
    RETRY_DELAY = 1.0

    def _wait_for_xtts_server(self) -> bool:
        """Wait for XTTS server to be available"""
        for attempt in range(self.MAX_RETRIES):
            try:
                response = httpx.get(f"{self.XTTS_SERVER_URL}/health", timeout=5.0)
                if response.status_code == 200:
                    health = response.json()
                    if health.get("model_loaded"):
                        return True
            except Exception:
                pass

            if attempt < self.MAX_RETRIES - 1:
                time.sleep(self.RETRY_DELAY)

        return False

    def generate_base_audio(
        self,
        *,
        text: str,
        language: str,
        output_path: Path,
        model: str | None = None,
        emotion: str | None = None,
        speed: float = 1.0,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.8,
        repetition_penalty: float = 2.0,
        speaker_wav: str | None = None,
        use_gpu: bool = True,
        gpu_device: str = "auto",
        timeout: int | None = None,
    ) -> Path:
        """Generate audio using the XTTS Docker server"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Wait for XTTS server to be available
        if not self._wait_for_xtts_server():
            raise RuntimeError(
                f"XTTS server is not available at {self.XTTS_SERVER_URL}. "
                "Make sure the XTTS Docker container is running: docker run -d -p 8001:8001 xtts-server:latest"
            )

        # Get speaker wav path
        speaker_wav = speaker_wav or os.getenv("VOICE_ENGINE_XTTS_SPEAKER_WAV")
        if not speaker_wav:
            default_speaker = settings.xtts_models_dir / "speaker.wav"
            if default_speaker.exists():
                speaker_wav = str(default_speaker)

        if not speaker_wav:
            raise RuntimeError(
                "No speaker_wav file found. Set VOICE_ENGINE_XTTS_SPEAKER_WAV environment variable or place speaker.wav in models/xtts/"
            )

        # Convert Windows path to Docker container path
        # The XTTS Docker container mounts the volume at /app/data
        # So we always send the Docker internal path, not the host path
        docker_speaker_path = "/app/data/speaker.wav"

        # Prepare request payload
        payload = {
            "text": text,
            "language": language,
            "speaker_wav": docker_speaker_path,  # Use Docker internal path
        }

        # Call XTTS server
        try:
            with httpx.Client(timeout=timeout or 300.0) as client:
                response = client.post(
                    f"{self.XTTS_SERVER_URL}/generate",
                    json=payload,
                )

            if response.status_code != 200:
                error_detail = response.json().get("detail", "Unknown error")
                raise RuntimeError(f"XTTS server error: {error_detail}")

            result = response.json()
            generated_file_docker = result.get("file")  # e.g., /app/data/tts_xxxxx.wav

            if not generated_file_docker:
                raise RuntimeError(f"XTTS server did not return a file path")

            # Convert Docker path to host path for file access
            # Docker path: /app/data/tts_xxxxx.wav
            # Host path: app/runtime/datasets/tts_xxxxx.wav
            if generated_file_docker.startswith("/app/data/"):
                filename = generated_file_docker.replace("/app/data/", "")
                generated_file = settings.datasets_dir / filename
            else:
                generated_file = Path(generated_file_docker)

            if not generated_file.exists():
                raise RuntimeError(f"XTTS server file not found at {generated_file}")

            # Copy generated file to output path
            shutil.copy2(generated_file, output_path)

            return output_path

        except httpx.TimeoutException:
            raise RuntimeError(f"XTTS server request timed out after {timeout or 300} seconds")
        except Exception as e:
            raise RuntimeError(f"Failed to generate audio with XTTS: {str(e)}")


xtts_service = XTTSService()
