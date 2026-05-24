#!/usr/bin/env python3
"""
Direct RVC Training - Skip to model training with correct epochs
"""

import sys
import os

sys.path.insert(0, os.getcwd())

from app.backend.services.rvc_service import rvc_service

def main():
    print("=" * 70)
    print("RVC Model Training - esposa_voice (Direct)")
    print("=" * 70)

    voice_name = "esposa_voice"

    # Step 1: Train model with CORRECTED epochs
    print("\n[1/2] Training RVC model (200 epochs, ~2.5 hours)...")
    try:
        result = rvc_service.train(
            voice_name=voice_name,
            sample_rate="40k",
            epochs=200,
            batch_size=1,
            learning_rate=0.0001,
            save_every_epoch=10,
            mixed_precision=False,
            version="v2",
            use_gpu=False,
            gpu_device="auto",
            timeout=36000  # 10 hour timeout for 200 epochs
        )
        print("[OK] Model training complete")
        print(f"  Training results: {result}")
    except Exception as e:
        print(f"[FAIL] Model training failed: {e}")
        return False

    # Step 2: Build FAISS index
    print("\n[2/2] Building FAISS index (for fast voice conversion)...")
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
    print(f"  FAISS index: app/models/voices/{voice_name}/model.index")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
