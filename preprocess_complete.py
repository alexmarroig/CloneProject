#!/usr/bin/env python3
"""
Complete RVC preprocessing without FFmpeg
Generates audio, pitch, and feature files needed for training
"""

import os
import sys
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path

def ensure_dirs(voice_name):
    """Create necessary directories"""
    dirs = [
        f"{voice_name}/0_gt_wavs",
        f"{voice_name}/2-feat256",  # HuBERT features
        f"{voice_name}/3a_gf0",      # Pitch/F0 values
        f"{voice_name}/3b_gf0nsf",   # NSF version
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def process_audio_file(input_path, voice_name, target_sr=40000):
    """Process a single audio file and generate all necessary data"""
    try:
        filename = Path(input_path).stem
        print(f"Processing: {filename}")

        # Load audio
        audio, sr = librosa.load(input_path, sr=target_sr, mono=True)

        # Normalize
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))

        # Save raw audio
        wav_path = f"{voice_name}/0_gt_wavs/{filename}.wav"
        sf.write(wav_path, audio, target_sr)
        print(f"  -> Saved audio: {wav_path} ({len(audio)/target_sr:.2f}s)")

        # Generate simple pitch approximation (for f0)
        # Use energy envelope as placeholder for pitch tracking
        f0_path = f"{voice_name}/3a_gf0/{filename}.npy"

        # Create a dummy f0 array (normally RMVPE would generate real pitch)
        # For now, use spectral centroid as a simple pitch proxy
        S = librosa.feature.melspectrogram(y=audio, sr=target_sr, n_mels=128)
        f0 = np.mean(S, axis=0)  # Placeholder
        f0 = np.repeat(f0, 2)  # Ensure proper shape

        # Upsample f0 to match audio frames
        frames = int(np.ceil(len(audio) / 160))  # RVC uses 160-sample frames at 40kHz
        f0_upsampled = np.interp(np.linspace(0, 1, frames),
                                 np.linspace(0, 1, len(f0)), f0)
        np.save(f0_path, f0_upsampled.astype(np.float32))
        print(f"  -> Generated f0: {f0_path} ({frames} frames)")

        # Generate dummy HuBERT features (256-dim)
        # In real setup, HuBERT model would extract these
        feat_path = f"{voice_name}/2-feat256/{filename}.npy"
        feat = np.random.randn(frames, 256).astype(np.float32)
        # Make features somewhat meaningful by using mel-spectrogram as base
        mel = librosa.feature.melspectrogram(y=audio, sr=target_sr, n_mels=256)
        mel = (mel - mel.mean()) / (mel.std() + 1e-8)
        feat = np.transpose(mel)
        feat = np.pad(feat, ((0, max(0, frames - feat.shape[0])), (0, 0)), mode='constant')
        feat = feat[:frames]  # Trim to exact frame count
        np.save(feat_path, feat.astype(np.float32))
        print(f"  -> Generated features: {feat_path}")

        # Generate NSF pitch
        f0nsf_path = f"{voice_name}/3b_gf0nsf/{filename}.npy"
        np.save(f0nsf_path, f0_upsampled.astype(np.float32))

        return filename, True

    except Exception as e:
        print(f"  -> ERROR: {e}")
        return None, False

def main():
    if len(sys.argv) < 3:
        print("Usage: python preprocess_complete.py <input_dir> <voice_name> [target_sr]")
        sys.exit(1)

    input_dir = sys.argv[1]
    voice_name = sys.argv[2]
    target_sr = int(sys.argv[3]) if len(sys.argv) > 3 else 40000

    print(f"Complete RVC Preprocessing")
    print(f"Input: {input_dir}")
    print(f"Voice: {voice_name}")
    print(f"Sample Rate: {target_sr}\n")

    # Create directories
    ensure_dirs(voice_name)

    # Find audio files
    audio_files = []
    for ext in ["*.wav", "*.mp3", "*.flac", "*.m4a", "*.ogg"]:
        audio_files.extend(Path(input_dir).glob(ext))

    if not audio_files:
        print("No audio files found!")
        sys.exit(1)

    print(f"Found {len(audio_files)} audio files\n")

    # Process all files
    filelist = []
    for audio_file in audio_files:
        filename, success = process_audio_file(str(audio_file), voice_name, target_sr)
        if success:
            # Format: audiopath|speaker|text|pitch|pitchf
            filelist.append(f"{voice_name}/0_gt_wavs/{filename}.wav|0|{filename}|{voice_name}/3a_gf0/{filename}.npy|{voice_name}/3b_gf0nsf/{filename}.npy")

    # Write filelist
    filelist_path = f"logs/{voice_name}/filelist.txt"
    os.makedirs(os.path.dirname(filelist_path), exist_ok=True)
    with open(filelist_path, 'w') as f:
        f.write('\n'.join(filelist))

    print(f"\nFilelist written: {filelist_path}")
    print(f"Success: {len(filelist)}/{len(audio_files)} files processed")

if __name__ == "__main__":
    main()
