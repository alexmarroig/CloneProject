from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.backend.core.settings import settings
from app.backend.routers.voice_engine import router as voice_engine_router

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(voice_engine_router)

# Serve static files (CSS, JS, images)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Serve audio output
app.mount("/audio", StaticFiles(directory=settings.audio_output_dir), name="audio")

# Serve the main HTML page
@app.get("/")
async def serve_index():
    index_path = Path(__file__).parent.parent / "static" / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Web UI not found. Create app/static/index.html"}
