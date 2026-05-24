#!/usr/bin/env python3
"""
Simple RVC inference wrapper
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("="*70)
    print("RVC Voice Conversion - Apply Wife's Voice")
    print("="*70)
    print()

    input_file = "tts_temp.mp3"
    model_name = "esposa_voice"
    output_file = "reels_audio_esposa_voice.wav"

    # Check if input exists
    if not Path(input_file).exists():
        print(f"[ERROR] Input file not found: {input_file}")
        return False

    print(f"Input: {input_file}")
    print(f"Model: {model_name}")
    print(f"Output: {output_file}")
    print()

    # Try using RVC's infer-web.py if it exists
    infer_script = Path("infer-web.py")

    if infer_script.exists():
        print("[INFO] Using RVC inference script...")
        print()
        print("Running voice conversion (this may take a minute)...")

        cmd = [
            sys.executable,
            str(infer_script),
            "--f0up_key", "0",
            "--input_path", input_file,
            "--index_path", f"assets/weights/{model_name}.index",
            "--model_name", model_name,
            "--output_path", output_file,
            "--pth_path", f"assets/weights/{model_name}.pth"
        ]

        result = subprocess.run(cmd, capture_output=False)

        if result.returncode == 0 and Path(output_file).exists():
            size_mb = Path(output_file).stat().st_size / (1024 * 1024)
            print()
            print("="*70)
            print("[OK] VOICE CONVERSION COMPLETE!")
            print("="*70)
            print(f"Output: {Path(output_file).absolute()}")
            print(f"Size: {size_mb:.1f} MB")
            return True
        else:
            print("[ERROR] Voice conversion failed")
            return False
    else:
        print("[ERROR] RVC inference script not found")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
