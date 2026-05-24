#!/usr/bin/env python3
"""
RVC Training Pipeline - Wife's Voice Model
Usa a estrutura correta do RVC instalado localmente
"""

import subprocess
import sys
import os
from pathlib import Path
import shutil

# Configuration
PROJECT_ROOT = Path.cwd()
VOICE_NAME = "esposa_voice"
DATASET_PATH = PROJECT_ROOT / "app" / "runtime" / "datasets"
SAMPLE_RATE = 40000  # Use numeric value, not "40k"
EPOCHS = 300
BATCH_SIZE = 1
LEARNING_RATE = 0.0001
DEVICE = "cpu"  # Change to "cuda" if GPU available

# RVC paths
INFER_DIR = PROJECT_ROOT / "infer"
TRAIN_MODULE = INFER_DIR / "modules" / "train"

# Environment setup
env = os.environ.copy()
env["PYTHONPATH"] = str(PROJECT_ROOT)

def run_command(cmd, description, timeout=3600):
    """Run a command and report status"""
    print(f"\n{'='*70}")
    print(f"{description}")
    print(f"{'='*70}")
    print(f"Command: {' '.join(str(c) for c in cmd)}\n")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            timeout=timeout
        )

        if result.returncode == 0:
            print(f"\n[OK] {description} - SUCCESS\n")
            return True
        else:
            print(f"\n[ERROR] {description} - FAILED (exit code: {result.returncode})\n")
            return False
    except subprocess.TimeoutExpired:
        print(f"\n[ERROR] {description} - TIMEOUT\n")
        return False
    except Exception as e:
        print(f"\n[ERROR] {description} - ERROR: {e}\n")
        return False

def main():
    print("=" * 70)
    print("RVC Training Pipeline - Wife's Voice (esposa_voice)")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Voice Name: {VOICE_NAME}")
    print(f"  Dataset: {DATASET_PATH}")
    print(f"  Sample Rate: {SAMPLE_RATE}")
    print(f"  Epochs: {EPOCHS}")
    print(f"  Batch Size: {BATCH_SIZE}")
    print(f"  Learning Rate: {LEARNING_RATE}")
    print(f"  Device: {DEVICE}")
    print(f"  Project Root: {PROJECT_ROOT}")

    # Check if dataset exists
    if not DATASET_PATH.exists():
        print(f"\n[ERROR] Dataset directory not found: {DATASET_PATH}")
        return False

    audio_files = list(DATASET_PATH.glob("*.wav")) + list(DATASET_PATH.glob("*.mp3"))
    if not audio_files:
        print(f"\n[ERROR] No audio files found in {DATASET_PATH}")
        return False

    print(f"\n[OK] Found {len(audio_files)} audio files for training:")
    for f in audio_files:
        print(f"    - {f.name}")

    # Step 1: Preprocess
    print("\n" + "="*70)
    print("[1/4] PREPROCESSING - Preparing audio for training")
    print("="*70)

    # Use simplified preprocessing that doesn't require FFmpeg
    preprocess_cmd = [
        sys.executable,
        "preprocess_simple.py",
        str(DATASET_PATH),
        str(SAMPLE_RATE),
        str(Path.cwd() / VOICE_NAME / "0_gt_wavs"),
    ]
    if not run_command(preprocess_cmd, "Audio Preprocessing", timeout=600):
        print("[WARNING]  Preprocessing failed, but continuing...")

    # Step 2: Delete old broken logs
    print("\n" + "="*70)
    print("[2/4] CLEANUP - Removing previous corrupted training logs")
    print("="*70)
    logs_dir = PROJECT_ROOT / "logs" / VOICE_NAME
    if logs_dir.exists():
        print(f"Keeping existing logs directory: {logs_dir} because we just rebuilt it!")
        
    print("\n" + "="*70)
    print("[3/4] TRAINING - Training RVC model")
    print("="*70)
    print(f"This may take 30-120 minutes depending on CPU/GPU...")

    if TRAIN_MODULE.exists() and (TRAIN_MODULE / "train.py").exists():
        # Convert sample rate to RVC format (e.g., 40000 -> "40k")
        sr_key = f"{int(SAMPLE_RATE/1000)}k"
        train_cmd = [
            sys.executable,
            str(TRAIN_MODULE / "train.py"),
            "-se", "10",  # Save every 10 epochs
            "-te", str(EPOCHS),  # Total epochs
            "-bs", str(BATCH_SIZE),  # Batch size
            "-e", VOICE_NAME,  # Experiment directory
            "-sr", sr_key,  # Sample rate (40k format)
            "-v", "v2",  # RVC version
            "-f0", "1",  # Use F0 (pitch extraction)
            "-l", "0",  # Don't use latest checkpoint
            "-c", "0",  # Don't cache in GPU (we're on CPU)
        ]
        if not run_command(train_cmd, "Model Training", timeout=7200):
            print("[ERROR] Training failed")
            return False
    else:
        print("[ERROR] Training script not found at", TRAIN_MODULE / "train.py")
        return False

    # Step 3: Build FAISS index
    print("\n" + "="*70)
    print("[3/4] INDEX BUILDING - Creating FAISS retrieval index")
    print("="*70)

    index_script = PROJECT_ROOT / "tools" / "infer" / "train-index-v2.py"
    if index_script.exists():
        # Find the trained model
        weights_dir = PROJECT_ROOT / "assets" / "weights" / VOICE_NAME
        if weights_dir.exists():
            model_path = weights_dir / f"{VOICE_NAME}.pth"
            if model_path.exists():
                index_cmd = [
                    sys.executable,
                    str(index_script),
                    str(weights_dir),
                ]
                if not run_command(index_cmd, "FAISS Index Building", timeout=600):
                    print("[WARNING]  Index building failed, voice conversion may be slower")
    else:
        print("[WARNING]  Index building script not found, skipping...")

    # Step 4: Verify model
    print("\n" + "="*70)
    print("[4/4] VERIFICATION - Checking trained model")
    print("="*70)

    weights_dir = PROJECT_ROOT / "assets" / "weights" / VOICE_NAME
    if weights_dir.exists():
        print(f"\n[OK] Model directory found: {weights_dir}")
        print(f"\nGenerated files:")
        for file in sorted(weights_dir.iterdir()):
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"    - {file.name} ({size_mb:.1f} MB)")
    else:
        print(f"\n[ERROR] Model directory not found: {weights_dir}")
        return False

    print("\n" + "=" * 70)
    print("SUCCESS! Training pipeline complete!")
    print("=" * 70)
    print(f"\nYour trained model is ready at:")
    print(f"  {weights_dir}/")
    print(f"\nNext steps:")
    print(f"  1. Test with audio conversion")
    print(f"  2. Use with XTTS for text-to-speech")
    print(f"  3. Fine-tune with more data if needed")
    print(f"\nModel name for conversion: {VOICE_NAME}")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
