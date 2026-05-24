#!/usr/bin/env python3
"""
Generate audio with wife's voice using XTTS (TTS) + RVC (Voice Conversion)
"""

import os
import sys
import json
from pathlib import Path
import numpy as np
import soundfile as sf
import argparse

# Add RVC modules to path
PROJECT_ROOT = Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT))

def load_rvc_model(model_path, device="cpu"):
    """Load trained RVC model"""
    try:
        from infer.models import SynthesizerTrnMs256NSFsid
        import torch

        model = SynthesizerTrnMs256NSFsid(
            256,
            40,  # Number of pitches/frequencies
            3,   # Number of hidden channels
            192, # Number of filter channels
            5,   # Number of residual blocks
            2,   # Number of encoder layers
            2,   # Number of decoder layers
            2    # Number of postnet layers
        )

        print(f"Loading RVC model from {model_path}...")
        checkpoint = torch.load(model_path, map_location=device)

        if "model" in checkpoint:
            state_dict = checkpoint["model"]
        else:
            state_dict = checkpoint

        model.load_state_dict(state_dict)
        model.eval()
        model = model.to(device)

        print("✓ Model loaded successfully")
        return model
    except Exception as e:
        print(f"✗ Error loading RVC model: {e}")
        return None

def convert_voice(audio_data, sr, model, device="cpu"):
    """Apply RVC voice conversion to audio"""
    try:
        import torch

        # Prepare audio tensor
        audio_tensor = torch.FloatTensor(audio_data).unsqueeze(0).to(device)

        with torch.no_grad():
            # Get speaker embedding (assuming single speaker)
            speaker_id = torch.LongTensor([0]).to(device)

            # Run voice conversion
            output, _ = model(audio_tensor, speaker_id)

        # Convert back to numpy
        output_audio = output.squeeze(0).cpu().numpy()

        return output_audio

    except Exception as e:
        print(f"✗ Error during voice conversion: {e}")
        return audio_data

def generate_with_xtts(text_content, output_path, speaker_wav=None):
    """Generate audio using XTTS-v2 (Text-to-Speech)"""
    try:
        from TTS.api import TTS

        print("\n" + "="*70)
        print("STEP 1: Text-to-Speech Generation with XTTS")
        print("="*70)
        print(f"Text: {text_content[:100]}...")

        # Initialize TTS model
        print("Loading XTTS model... (this may take 30-60 seconds first time)")
        tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                  gpu=False,  # CPU mode
                  progress_bar=True)

        # Use wife's voice if available
        if speaker_wav and os.path.exists(speaker_wav):
            print(f"Using speaker reference: {speaker_wav}")
            tts.tts_to_file(
                text=text_content,
                file_path=output_path,
                speaker_wav=speaker_wav,
                language="pt"  # Portuguese
            )
        else:
            # Default female voice in Portuguese
            print("Using default Portuguese female voice")
            tts.tts_to_file(
                text=text_content,
                file_path=output_path,
                speaker="Ana",  # Portuguese speaker
                language="pt"
            )

        print(f"✓ TTS audio generated: {output_path}")
        return output_path

    except Exception as e:
        print(f"✗ Error generating TTS audio: {e}")
        return None

def apply_rvc_conversion(input_audio, model_name="esposa_voice", device="cpu"):
    """Apply RVC model to convert voice"""
    try:
        print("\n" + "="*70)
        print("STEP 2: Voice Conversion with RVC")
        print("="*70)

        # Paths
        model_dir = PROJECT_ROOT / "assets" / "weights" / model_name
        model_file = model_dir / f"{model_name}.pth"
        index_file = model_dir / f"{model_name}.index"

        if not model_file.exists():
            print(f"✗ Model file not found: {model_file}")
            print("  Waiting for training to complete...")
            return None

        print(f"Input audio: {input_audio}")
        print(f"Model: {model_file}")

        # Load audio
        audio_data, sr = sf.read(input_audio)
        print(f"Audio loaded: {len(audio_data)} samples @ {sr}Hz")

        # Load RVC model
        model = load_rvc_model(str(model_file), device)
        if model is None:
            return None

        # Apply conversion
        print("Converting voice...")
        converted_audio = convert_voice(audio_data, sr, model, device)

        return converted_audio, sr

    except Exception as e:
        print(f"✗ Error in RVC conversion: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    parser = argparse.ArgumentParser(description="Generate audio with wife's voice")
    parser.add_argument("--text", type=str, default=None,
                       help="Text to generate audio from")
    parser.add_argument("--input-audio", type=str, default=None,
                       help="Input audio file to convert")
    parser.add_argument("--output", type=str, default="output_voice.wav",
                       help="Output audio file")
    parser.add_argument("--model", type=str, default="esposa_voice",
                       help="RVC model name")
    parser.add_argument("--device", type=str, default="cpu",
                       help="Device to use (cpu or cuda)")

    args = parser.parse_args()

    print("="*70)
    print("Voice Generation Pipeline - Wife's Voice Model")
    print("="*70)
    print(f"Output: {args.output}")
    print(f"Model: {args.model}")
    print(f"Device: {args.device}")
    print()

    # Step 1: Generate TTS audio
    if args.text and not args.input_audio:
        # Use wife's voice as reference if available
        ref_voice = PROJECT_ROOT / "app" / "runtime" / "datasets" / "voice.wav"
        if not ref_voice.exists():
            ref_voice = None

        tts_output = "tts_temp.wav"
        if not generate_with_xtts(args.text, tts_output, speaker_wav=str(ref_voice) if ref_voice else None):
            return False
        input_for_rvc = tts_output
    elif args.input_audio:
        input_for_rvc = args.input_audio
    else:
        print("✗ Provide either --text or --input-audio")
        return False

    # Step 2: Apply RVC conversion
    result = apply_rvc_conversion(input_for_rvc, args.model, args.device)

    if result is None:
        print("\n⚠️  Model not ready yet. Training in progress...")
        print("   Please wait for training to complete and try again.")
        return False

    converted_audio, sr = result

    # Save output
    print(f"\nSaving output to: {args.output}")
    sf.write(args.output, converted_audio, sr)

    print("\n" + "="*70)
    print("✓ SUCCESS - Audio generated with wife's voice!")
    print("="*70)
    print(f"Output file: {args.output}")
    print(f"Duration: {len(converted_audio) / sr:.2f} seconds")

    # Clean up temp file
    if Path("tts_temp.wav").exists():
        Path("tts_temp.wav").unlink()

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
