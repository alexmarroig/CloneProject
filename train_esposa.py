#!/usr/bin/env python3
"""
Complete RVC Training Pipeline for Wife's Voice
Treina um modelo RVC com a voz da esposa
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.getcwd())

from app.backend.services.rvc_service import rvc_service

def main():
    print("=" * 70)
    print("RVC Training Pipeline - esposa_voice")
    print("=" * 70)

    voice_name = "esposa_voice"
    dataset_path = "app/runtime/datasets/"

    # Step 1: Preprocess
    print("\n[1/5] Preprocessing audio (silence trimming, normalization)...")
    try:
        rvc_service.preprocess(
            voice_name=voice_name,
            dataset_path=dataset_path,
            sample_rate="40k",
            silence_slicing=True,
            normalize=True,
            min_audio_seconds=1.0,
            max_audio_seconds=300.0,
            timeout=600
        )
        print("[OK] Preprocessing complete")
    except Exception as e:
        print(f"[FAIL] Preprocessing failed: {e}")
        return False

    # Step 2: Extract pitch
    print("\n[2/5] Extracting pitch (RMVPE method)...")
    try:
        rvc_service.extract_pitch(
            voice_name=voice_name,
            f0_method="rmvpe",
            timeout=600
        )
        print("[OK] Pitch extraction complete")
    except Exception as e:
        print(f"[FAIL] Pitch extraction failed: {e}")
        return False

    # Step 3: Extract features
    print("\n[3/5] Extracting features (HuBERT embeddings)...")
    try:
        rvc_service.extract_features(
            voice_name=voice_name,
            version="v2",
            use_gpu=False,
            gpu_device="auto",
            timeout=600
        )
        print("[OK] Feature extraction complete")
    except Exception as e:
        print(f"[FAIL] Feature extraction failed: {e}")
        return False

    # Step 4: Train model
    print("\n[4/5] Training RVC model (300 epochs, this will take 30-90 minutes)...")
    try:
        result = rvc_service.train(
            voice_name=voice_name,
            sample_rate="40k",
            epochs=300,
            batch_size=1,
            learning_rate=0.0001,
            save_every_epoch=10,
            mixed_precision=False,
            version="v2",
            use_gpu=False,
            gpu_device="auto",
            timeout=3600  # 1 hour timeout
        )
        print("[OK] Model training complete")
        print(f"  Training results: {result}")
    except Exception as e:
        print(f"[FAIL] Model training failed: {e}")
        return False

    # Step 5: Build FAISS index
    print("\n[5/5] Building FAISS index (for fast voice conversion)...")
    try:
        result = rvc_service.build_index(
            voice_name=voice_name,
            version="v2",
            timeout=600
        )
        print("[OK] FAISS index built successfully")
        print(f"  Index result: {result}")
    except Exception as e:
        print(f"[FAIL] Index building failed: {e}")
        return False

    print("\n" + "=" * 70)
    print("SUCCESS! Training pipeline complete!")
    print("=" * 70)
    print(f"\nYour trained model is ready:")
    print(f"  Model file: assets/weights/{voice_name}/")
    print(f"  Name: {voice_name}")
    print(f"\nYou can now use this model to:")
    print(f"  1. Convert any audio to your wife's voice")
    print(f"  2. Generate speech in your wife's voice")
    print(f"\nNext steps:")
    print(f"  - Test the model with sample audio")
    print(f"  - Adjust parameters if needed")
    print(f"  - Use with XTTS for text-to-speech conversion")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
