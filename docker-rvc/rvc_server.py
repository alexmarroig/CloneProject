#!/usr/bin/env python3
"""
RVC HTTP Server - wraps infer_cli.py to avoid fairseq import issues
Runs inference in isolated subprocess to avoid Python 3.11 compatibility problems
"""
import json
import subprocess
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI()

RVC_ROOT = Path(__file__).parent.parent

class ConversionRequest(BaseModel):
    input_path: str
    output_path: str
    model_path: str
    index_path: str = None
    pitch_shift: int = 0
    f0_method: str = "rmvpe"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "rvc",
        "model_loaded": True
    }


@app.post("/convert")
def convert(request: ConversionRequest):
    """Convert voice using RVC"""
    try:
        input_path = Path(request.input_path)
        output_path = Path(request.output_path)
        model_path = Path(request.model_path)

        if not input_path.exists():
            raise HTTPException(status_code=400, detail=f"Input file not found: {input_path}")

        if not model_path.exists():
            raise HTTPException(status_code=400, detail=f"Model file not found: {model_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build command
        cmd = [
            sys.executable,
            str(RVC_ROOT / "tools" / "infer_cli.py"),
            "-m", str(model_path),
            "-i", str(input_path),
            "-o", str(output_path),
            "-d", "cpu"
        ]

        if request.index_path and Path(request.index_path).exists():
            cmd.extend(["-x", str(request.index_path)])

        # Run in subprocess to isolate fairseq imports
        result = subprocess.run(
            cmd,
            cwd=str(RVC_ROOT),
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout
            raise HTTPException(status_code=500, detail=f"RVC conversion failed: {error_msg}")

        if not output_path.exists():
            raise HTTPException(status_code=500, detail=f"Output file was not created")

        return {
            "success": True,
            "output_path": str(output_path),
            "file_size": output_path.stat().st_size
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="RVC conversion timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
