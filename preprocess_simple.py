#!/usr/bin/env python3
"""
Simplified audio preprocessing using librosa (no FFmpeg required)
Converts audio files to the target sample rate and saves them
"""

import os
import sys
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path

def preprocess_audio(input_path, output_dir, target_sr=40000, force_mono=True):
    """
    Load audio, resample, and save to output directory
    """
    try:
        print(f"Processing: {input_path}")

        # Load audio with librosa (handles various formats without FFmpeg)
        audio, sr = librosa.load(input_path, sr=target_sr, mono=force_mono)

        # Normalize audio
        audio = audio / np.max(np.abs(audio))

        # Save processed audio
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, Path(input_path).stem + ".wav")
        sf.write(output_path, audio, target_sr)

        print(f"  -> Saved: {output_path} ({len(audio) / sr:.2f}s)")
        return True
    except Exception as e:
        print(f"  -> ERROR: {e}")
        return False

def main():
    if len(sys.argv) < 4:
        print("Usage: python preprocess_simple.py <input_dir> <target_sr> <output_dir>")
        sys.exit(1)

    input_dir = sys.argv[1]
    target_sr = int(sys.argv[2])
    output_dir = sys.argv[3]

    print(f"Preprocessing audio files from: {input_dir}")
    print(f"Target sample rate: {target_sr}")
    print(f"Output directory: {output_dir}")

    # Find audio files
    audio_files = []
    for ext in ["*.wav", "*.mp3", "*.flac", "*.m4a", "*.ogg"]:
        audio_files.extend(Path(input_dir).glob(ext))

    if not audio_files:
        print("No audio files found!")
        sys.exit(1)

    print(f"Found {len(audio_files)} audio files\n")

    # Process each file
    success_count = 0
    for audio_file in audio_files:
        if preprocess_audio(str(audio_file), output_dir, target_sr):
            success_count += 1

    print(f"\n{success_count}/{len(audio_files)} files processed successfully")

if __name__ == "__main__":
    main()
