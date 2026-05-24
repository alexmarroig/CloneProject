#!/usr/bin/env python3
"""
Monitor RVC training progress
"""

import os
import time
from pathlib import Path
from datetime import datetime

def check_progress():
    """Check training progress"""
    print("="*70)
    print("RVC Training Progress Monitor")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print()

    # Check if training is running
    weights_dir = Path("assets/weights/esposa_voice")
    model_file = weights_dir / "esposa_voice.pth"

    print("[Dataset]")
    dataset_dir = Path("esposa_voice/0_gt_wavs")
    if dataset_dir.exists():
        audio_files = list(dataset_dir.glob("*.wav"))
        print(f"  [OK] Audio files: {len(audio_files)}")
        for f in audio_files[:3]:
            print(f"    - {f.name}")
        if len(audio_files) > 3:
            print(f"    ... and {len(audio_files) - 3} more")
    else:
        print(f"  [IN PROGRESS] Preprocessing in progress...")

    print("\n[Model Training]")
    if weights_dir.exists():
        checkpoints = list(weights_dir.glob("*.pth"))
        if checkpoints:
            latest = max(checkpoints, key=lambda p: p.stat().st_mtime)
            size_mb = latest.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(latest.stat().st_mtime)
            print(f"  [OK] Latest checkpoint: {latest.name}")
            print(f"    Size: {size_mb:.1f} MB")
            print(f"    Created: {mtime.strftime('%H:%M:%S')}")

            # Count checkpoints to estimate progress
            epoch = int(latest.stem.split("_")[-1]) if "_" in latest.stem else 0
            if epoch > 0:
                progress = (epoch / 300) * 100
                print(f"    Epoch: {epoch}/300 ({progress:.1f}% complete)")
        else:
            print(f"  [IN PROGRESS] Training starting...")
    else:
        print(f"  [IN PROGRESS] Creating model directory...")

    print("\n[FAISS Index]")
    index_file = weights_dir / "esposa_voice.index"
    if index_file.exists():
        size_mb = index_file.stat().st_size / (1024 * 1024)
        print(f"  [OK] Index built: {size_mb:.1f} MB")
    else:
        print(f"  [WAITING] Waiting for training completion...")

    print("\n[Training Log]")
    log_file = Path("training.log")
    if log_file.exists():
        with open(log_file, "r") as f:
            lines = f.readlines()
            if lines:
                # Show last 10 lines
                print("  Last updates:")
                for line in lines[-10:]:
                    line = line.strip()
                    if line:
                        print(f"    {line[:65]}")
    else:
        print("  No log file yet")

    print("\n" + "="*70)
    print("[Status Summary]")
    print("="*70)

    if model_file.exists():
        print("[OK] MODEL READY FOR INFERENCE!")
        print("\nYou can now generate audio. Run:")
        print("  python create_reels_audio.py")
    else:
        if weights_dir.exists() and list(weights_dir.glob("*.pth")):
            print("[IN PROGRESS] TRAINING IN PROGRESS")
            print("   Checkpoints are being created regularly")
            print(f"\n   Check back soon: python check_training_progress.py")
        else:
            print("[IN PROGRESS] TRAINING STARTING UP")
            print("   This may take a few minutes to initialize...")

    print()

if __name__ == "__main__":
    try:
        check_progress()
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
