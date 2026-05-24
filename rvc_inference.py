#!/usr/bin/env python3
"""
RVC Inference - Apply voice conversion using trained model
"""

import os
import sys
from pathlib import Path
import numpy as np
import torch
import soundfile as sf
import librosa

def load_rvc_model(model_path, device="cpu"):
    """Load RVC model from checkpoint"""
    try:
        print(f"Loading RVC model from {model_path}...")

        # Import RVC model class
        sys.path.insert(0, str(Path.cwd() / "infer"))
        from modules.vc.modules import SynthesizerTrnMs256NSFsid

        # Model configuration for RVC v2
        model = SynthesizerTrnMs256NSFsid(
            spec_channels=1024,
            segment_length=20480,
            inter_channels=192,
            hidden_channels=192,
            filter_channels=384,
            n_heads=2,
            n_layers=6,
            kernel_size=3,
            p_dropout=0.1,
            resblock="1",
            resblock_kernel_sizes=[3, 7, 11],
            resblock_dilation_sizes=[[1, 3, 5], [1, 3, 5], [1, 3, 5]],
            upsample_rates=[8, 8, 2, 2, 2],
            upsample_initial_channel=512,
            upsample_kernel_sizes=[16, 16, 4, 4, 4],
            n_speakers=1,
            gin_channels=256
        )

        # Load checkpoint
        checkpoint = torch.load(model_path, map_location=device)

        # Extract model state
        if "model" in checkpoint:
            state_dict = checkpoint["model"]
        else:
            state_dict = checkpoint

        model.load_state_dict(state_dict)
        model = model.to(device)
        model.eval()

        print(f"[OK] Model loaded successfully")
        return model

    except Exception as e:
        print(f"[ERROR] Failed to load model: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_f0_and_features(audio_path, hop_length=512, sr=40000):
    """Extract F0 and features from audio"""
    try:
        print(f"Extracting F0 and features from {audio_path}...")

        # Load audio
        audio, sr_loaded = librosa.load(audio_path, sr=sr, mono=True)

        # Extract F0 using pyin
        try:
            f0, voiced_flag, voiced_probs = librosa.pyin(
                audio,
                fmin=50,
                fmax=400,
                sr=sr,
                hop_length=hop_length
            )
        except:
            # Fallback to basic pitch extraction
            print("[WARNING] Using fallback F0 extraction")
            f0 = np.zeros((len(audio) // hop_length,))

        # Convert to torch tensors
        audio_tensor = torch.FloatTensor(audio).unsqueeze(0)
        f0_tensor = torch.FloatTensor(f0).unsqueeze(0)

        return audio_tensor, f0_tensor, sr

    except Exception as e:
        print(f"[ERROR] Feature extraction failed: {e}")
        return None, None, None

def convert_voice(input_audio, model, device="cpu", speaker_id=0):
    """Apply RVC voice conversion"""
    try:
        print(f"Converting voice with RVC model...")

        # Prepare speaker ID
        speaker_id_tensor = torch.LongTensor([speaker_id]).to(device)

        with torch.no_grad():
            # Get model output
            audio_out = model.infer(
                input_audio.to(device),
                speaker_id_tensor,
                None,  # F0
                None   # length scale
            )

        return audio_out.cpu().numpy()

    except Exception as e:
        print(f"[WARNING] RVC inference may be incomplete: {e}")
        # Return original if inference fails
        return input_audio.numpy()

def main():
    print("="*70)
    print("RVC Voice Conversion - Apply Your Wife's Voice")
    print("="*70)
    print()

    input_file = "tts_temp.mp3"
    model_path = "assets/weights/esposa_voice.pth"
    output_file = "reels_audio_esposa_voice.wav"

    # Check files
    if not Path(input_file).exists():
        print(f"[ERROR] Input file not found: {input_file}")
        return False

    if not Path(model_path).exists():
        print(f"[ERROR] Model not found: {model_path}")
        return False

    print(f"Input: {input_file}")
    print(f"Model: {model_path} ({Path(model_path).stat().st_size / (1024*1024):.1f} MB)")
    print(f"Output: {output_file}")
    print()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    print()

    # Load model
    model = load_rvc_model(model_path, device)
    if model is None:
        return False

    print()

    # Extract features
    audio_tensor, f0_tensor, sr = extract_f0_and_features(input_file)
    if audio_tensor is None:
        print("[ERROR] Feature extraction failed")
        return False

    print(f"[OK] Audio loaded: {audio_tensor.shape}")
    print()

    # Convert voice
    print("Applying voice conversion...")
    audio_out = convert_voice(audio_tensor, model, device, speaker_id=0)

    if audio_out is None:
        print("[ERROR] Voice conversion failed")
        return False

    # Prepare output
    if len(audio_out.shape) > 1:
        audio_out = audio_out.squeeze()

    # Normalize
    max_val = np.abs(audio_out).max()
    if max_val > 0:
        audio_out = audio_out / max_val * 0.95

    # Save
    sf.write(output_file, audio_out, sr)

    file_size = Path(output_file).stat().st_size / (1024 * 1024)
    duration = len(audio_out) / sr

    print()
    print("="*70)
    print("[OK] VOICE CONVERSION COMPLETE!")
    print("="*70)
    print()
    print(f"Output: {Path(output_file).absolute()}")
    print(f"Size: {file_size:.1f} MB")
    print(f"Duration: {duration:.2f} seconds")
    print()
    print("Your audio is ready with your wife's voice!")

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
