#!/usr/bin/env python3
"""
Simplified RVC worker that doesn't import fairseq until needed
This avoids the dataclass/OmegaConf initialization issues
"""
import json
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def convert_via_cli(payload: dict) -> dict:
    """Call RVC inference_cli.py directly"""
    try:
        input_path = Path(payload["input_path"])
        output_path = Path(payload["output_path"])
        model_path = Path(payload["model_path"])
        index_path = Path(payload.get("index_path", ""))

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build command with correct argument names
        model_name = model_path.stem  # Extract name without extension
        cmd = [
            sys.executable,
            str(ROOT / "tools" / "infer_cli.py"),
            "--model_name", model_name,
            "--input_path", str(input_path),
            "--opt_path", str(output_path),
            "--device", payload.get("torch_device", "cpu"),
            "--f0method", payload.get("f0_method", "rmvpe"),
            "--f0up_key", str(payload.get("pitch_shift", 0)),
            "--index_rate", str(payload.get("index_rate", 0.66)),
            "--filter_radius", str(payload.get("filter_radius", 3)),
            "--resample_sr", str(payload.get("resample_rate", 0)),
            "--rms_mix_rate", str(payload.get("rms_mix_rate", 1.0)),
            "--protect", str(payload.get("protect_consonants", 0.33)),
        ]

        if index_path and index_path.exists():
            cmd.extend(["--index_path", str(index_path)])

        # Run inference
        result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            return {
                "ok": False,
                "error": f"RVC inference failed: {result.stderr or result.stdout}"
            }

        if output_path.exists():
            return {
                "ok": True,
                "result": {
                    "output_path": str(output_path),
                    "success": True
                }
            }
        else:
            return {
                "ok": False,
                "error": f"Output file not created at {output_path}"
            }

    except Exception as e:
        return {"ok": False, "error": str(e)}


def daemon_loop():
    """Read JSON requests from stdin, process them, return JSON responses"""
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue

        try:
            payload = json.loads(line)
            mode = payload.get("mode", "convert")

            if mode == "convert":
                result = convert_via_cli(payload)
            else:
                result = {"ok": False, "error": f"Unknown mode: {mode}"}

            print(json.dumps(result, ensure_ascii=False), flush=True)

        except Exception as e:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        daemon_loop()
    else:
        print("Usage: python rvc_worker_simple.py --daemon")
