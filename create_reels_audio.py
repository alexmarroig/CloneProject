#!/usr/bin/env python3
"""
Create reels audio with wife's voice
Specific script for the psychology/self-care reels content
"""

import os
import sys
from pathlib import Path

# Text for the reels (already provided)
REELS_TEXT = """Você acha que cuidar de você mesma é egoísmo?
Escuta só: limite não é punição. Limite é proteção.
Quando você estabelece um limite, você não está machucando ninguém.
Você está dizendo 'isso não é aceitável para mim'.
Não confunda estabelecer limite com vingança ou frieza.
Limite saudável é amar a si mesma primeiro.
Se você só é feliz quando desaparece pelo outro, o problema não é você.
É a crença errada que te ensinaram sobre amor.
Amar alguém não significa aceitar tudo. Significa respeitar a si mesma."""

def check_training_status():
    """Check if model training is complete"""
    model_path = Path("assets/weights/esposa_voice.pth")

    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"[OK] Model found: {size_mb:.1f} MB")
        return True
    else:
        print("[WAITING] Model not ready yet. Training in progress...")
        return False

def main():
    print("="*70)
    print("Creating Reels Audio - Wife's Voice")
    print("="*70)
    print()

    # Check if model is ready
    print("[1/2] Checking model status...")
    if not check_training_status():
        print("\n[WARNING] Please wait for the model training to complete.")
        print("     This typically takes 3-8 hours on CPU.")
        print("\n     You can:")
        print("     - Wait for training to finish")
        print("     - Check progress by running: python train_wife_voice.py")
        return False

    print("\n[2/2] Generating audio...")
    print(f"Text length: {len(REELS_TEXT)} characters")
    print(f"Approximate duration: 40-60 seconds")
    print()

    # Import and run generation
    import subprocess

    output_file = "reels_audio_esposa_voice.wav"

    cmd = [
        sys.executable,
        "generate_voice_audio.py",
        "--text", REELS_TEXT,
        "--output", output_file,
        "--model", "esposa_voice",
        "--device", "cpu"
    ]

    print(f"Running: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=str(Path.cwd()))

    if result.returncode == 0:
        output_path = Path(output_file)
        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print("\n" + "="*70)
            print("[OK] REELS AUDIO CREATED SUCCESSFULLY!")
            print("="*70)
            print(f"\nOutput file: {output_path.absolute()}")
            print(f"File size: {size_mb:.1f} MB")
            print(f"\nYour reels audio is ready to use!")
            print("You can now:")
            print("  1. Download the file")
            print("  2. Edit in your preferred video editor")
            print("  3. Add to your reels/shorts")
            return True
    else:
        print("\n[ERROR] Error generating audio. Please check the logs above.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
