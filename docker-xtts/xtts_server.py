#!/usr/bin/env python3
"""
XTTS Text-to-Speech Server
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
from pathlib import Path
import torch
import uuid
import time
import traceback
import os

app = FastAPI(title="XTTS TTS Server")

# Use CPU (no CUDA)
device = "cpu"
model = None
model_loaded = False

class TTSRequest(BaseModel):
    text: str
    language: str = "pt"
    voice_file: str = None
    speaker_wav: str = None

def load_model():
    """Carrega o modelo XTTS v2"""
    global model, model_loaded
    if model_loaded:
        return

    print("=" * 60)
    print("CARREGANDO MODELO XTTS V2...")
    print("=" * 60)

    try:
        # Pre-accept the license by creating TTS cache directory structure
        os.environ['TTS_HOME'] = '/root/.local/share/TTS'
        os.environ['TTS_LICENSE_ACCEPTED'] = 'y'
        
        # Create the TTS home directory
        tts_home = Path(os.environ['TTS_HOME'])
        tts_home.mkdir(parents=True, exist_ok=True)
        
        # Create a marker file to indicate license was accepted
        license_file = tts_home / '.license_accepted'
        license_file.touch()
        
        # Import TTS after environment is set
        from TTS.api import TTS
        
        # Load model with stdin redirected to avoid interactive prompt
        import subprocess
        import sys
        
        # Create model loader in a way that bypasses the interactive prompt
        try:
            model = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False, progress_bar=True)
        except Exception as e:
            # If it still prompts, try with devnull stdin
            print(f"First attempt failed: {e}, trying alternative method...")
            raise
        
        model_loaded = True
        print("Modelo XTTS carregado com sucesso!")
        print("=" * 60)
    except Exception as e:
        print(f"Erro ao carregar modelo: {e}")
        traceback.print_exc()
        raise

@app.on_event("startup")
async def startup():
    """Executado ao iniciar o servidor"""
    load_model()

@app.get("/")
async def root():
    return {"message": "XTTS TTS Server", "status": "ok"}

@app.get("/health")
async def health():
    """Status do servidor"""
    return {
        "status": "ok",
        "device": device,
        "model": "xtts_v2",
        "model_loaded": model_loaded
    }

@app.post("/generate")
async def generate_tts(request: TTSRequest):
    """
    Gera áudio com XTTS

    Args:
        text: Texto para converter em fala
        language: Código do idioma (pt, en, es, etc)
        voice_file ou speaker_wav: Caminho para arquivo de referência (speaker.wav)
    """
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Modelo não carregado")

    try:
        output_id = str(uuid.uuid4())[:8]
        output_path = Path("/app/data") / f"tts_{output_id}.wav"

        # Usar voice_file ou speaker_wav
        speaker_wav = request.speaker_wav or request.voice_file or "/app/data/speaker.wav"

        # Verificar se o arquivo de referência existe
        if not Path(speaker_wav).exists():
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo de referência não encontrado: {speaker_wav}"
            )

        print(f"\n[{output_id}] Gerando TTS...")
        print(f"  Texto: {request.text[:50]}...")
        print(f"  Idioma: {request.language}")
        print(f"  Referência: {speaker_wav}")

        start_time = time.time()

        # Gerar áudio com XTTS
        model.tts_to_file(
            text=request.text,
            speaker_wav=speaker_wav,
            language=request.language,
            file_path=str(output_path)
        )

        elapsed = time.time() - start_time
        file_size = output_path.stat().st_size / (1024 * 1024)

        print(f"  Concluído em {elapsed:.1f}s")
        print(f"  Tamanho: {file_size:.2f} MB")

        return {
            "status": "success",
            "output_id": output_id,
            "file": str(output_path),
            "text": request.text[:100],
            "language": request.language,
            "duration_seconds": elapsed,
            "file_size_mb": round(file_size, 2)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"\nErro na geração: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar áudio: {str(e)[:200]}"
        )

@app.get("/download/{output_id}")
async def download(output_id: str):
    """Download do áudio gerado"""
    file_path = Path("/app/data") / f"tts_{output_id}.wav"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    return FileResponse(file_path, media_type="audio/wav", filename=f"tts_{output_id}.wav")

@app.get("/list")
async def list_files():
    """Lista arquivos gerados"""
    data_dir = Path("/app/data")
    files = sorted(data_dir.glob("tts_*.wav"), key=lambda x: x.stat().st_mtime, reverse=True)

    return {
        "total": len(files),
        "files": [
            {
                "id": f.stem.replace("tts_", ""),
                "name": f.name,
                "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                "created": f.stat().st_mtime
            }
            for f in files[:10]
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
