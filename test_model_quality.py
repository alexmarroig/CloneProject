#!/usr/bin/env python3
"""
Test the esposa_voice model for 2.8kHz noise issue
"""

import sys
import os

sys.path.insert(0, os.getcwd())

from app.backend.services.rvc_service import rvc_service

def test_model():
    print("=" * 70)
    print("Testing esposa_voice Model Quality")
    print("=" * 70)

    voice_name = "esposa_voice"
    test_input = "app/runtime/datasets/voice.wav"  # Use original training audio
    test_output = "test_quality_output.wav"
    model_path = f"app/models/voices/{voice_name}/model.pth"
    index_path = f"app/models/voices/{voice_name}/model.index"

    if not os.path.exists(test_input):
        print(f"[FAIL] Test input not found: {test_input}")
        return False

    if not os.path.exists(model_path):
        print(f"[FAIL] Model not found: {model_path}")
        return False

    if not os.path.exists(index_path):
        print(f"[FAIL] Index not found: {index_path}")
        return False

    print("\n[INFO] Testing voice conversion with existing model...")
    print(f"  Input: {test_input}")
    print(f"  Output: {test_output}")
    print(f"  Model: {model_path}")
    print(f"  Index: {index_path}")

    try:
        result = rvc_service.convert_voice(
            input_path=test_input,
            output_path=test_output,
            model_path=model_path,
            index_path=index_path,
            pitch_shift=0,  # No pitch shift
            f0_method="rmvpe",
            index_rate=0.66,
            filter_radius=3,
            resample_rate=0,
            rms_mix_rate=1.0,
            protect_consonants=0.33,
            use_gpu=False
        )
        print(f"[OK] Voice conversion complete")
        print(f"  Result: {result}")

        if os.path.exists(test_output):
            size_mb = os.path.getsize(test_output) / (1024 * 1024)
            print(f"  Output file size: {size_mb:.2f} MB")
            print(f"\n[SUCCESS] Audio test produced output: {test_output}")
            print("\n[INFO] To check for 2.8kHz noise:")
            print("  1. Open the audio file in an audio editor")
            print("  2. Check spectrogram for high-pitched noise around 2.8kHz")
            print("  3. Compare with original test_output_phase1.wav from Phase 1")
            return True
        else:
            print(f"[FAIL] Output file not created")
            return False

    except Exception as e:
        print(f"[FAIL] Voice conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_model()
    sys.exit(0 if success else 1)
