#!/usr/bin/env python3
"""
Phase 1 RVC Model Retraining Script
Retrains esposa_voice model with FP32 precision on CPU
Runs in background with logging
"""

import sys
import os
import logging
from pathlib import Path

# Setup path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "training_phase1.log"

# Configure logging to file and stdout
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

from app.backend.services.training_controller import training_controller
from app.backend.services.rvc_service import rvc_service


def main():
    """Main retraining pipeline"""

    logger.info("=" * 80)
    logger.info("PHASE 1: RVC Model Retraining with FP32")
    logger.info("=" * 80)

    # Verify configuration
    logger.info("\n[STEP 0] Verifying configuration...")
    if not training_controller.verify_config():
        logger.error("Configuration verification failed!")
        return False

    # Verify dataset
    dataset_path = "C:/Users/gaming/Desktop/dataset_alex/voice.wav"
    logger.info(f"\n[STEP 0.5] Verifying dataset...")
    if not training_controller.verify_dataset(dataset_path):
        logger.error("Dataset verification failed!")
        return False

    # Clean up old marker
    training_controller.cleanup_old_marker()

    voice_name = "esposa_voice"

    try:
        # Step 1: Preprocess
        logger.info("\n[STEP 1/5] Preprocessing audio (silence trimming, normalization)...")
        rvc_service.preprocess(
            voice_name=voice_name,
            dataset_path="C:/Users/gaming/Desktop/dataset_alex/",
            sample_rate="40k",
            silence_slicing=True,
            normalize=True,
            min_audio_seconds=1.0,
            max_audio_seconds=300.0,
            timeout=600
        )
        logger.info("[OK] Preprocessing complete")

        # Step 2: Extract pitch
        logger.info("\n[STEP 2/5] Extracting pitch (RMVPE method)...")
        rvc_service.extract_pitch(
            voice_name=voice_name,
            f0_method="rmvpe",
            timeout=600
        )
        logger.info("[OK] Pitch extraction complete")

        # Step 3: Extract features
        logger.info("\n[STEP 3/5] Extracting features (HuBERT embeddings)...")
        rvc_service.extract_features(
            voice_name=voice_name,
            version="v2",
            use_gpu=False,
            gpu_device="auto",
            timeout=600
        )
        logger.info("[OK] Feature extraction complete")

        # Step 4: Train model (THIS WILL TAKE 2-3 HOURS)
        logger.info("\n[STEP 4/5] Training RVC model (200 epochs, ~2.5 hours)...")
        logger.info("Training in progress... Monitor with: tail -f logs/training_phase1.log")

        result = rvc_service.train(
            voice_name=voice_name,
            sample_rate="40k",
            epochs=200,  # Reduced from 300 for faster training
            batch_size=1,
            learning_rate=0.0001,
            save_every_epoch=10,
            mixed_precision=False,  # Critical: Use FP32 on CPU
            version="v2",
            use_gpu=False,
            gpu_device="auto",
            timeout=14400  # 4 hour timeout (generous buffer)
        )
        logger.info("[OK] Model training complete")
        logger.info(f"Training results: {result}")

        # Step 5: Build FAISS index
        logger.info("\n[STEP 5/5] Building FAISS index (for fast voice conversion)...")
        result = rvc_service.build_index(
            voice_name=voice_name,
            version="v2",
            timeout=600
        )
        logger.info("[OK] FAISS index built successfully")
        logger.info(f"Index result: {result}")

        # Mark completion
        completion_marker = project_root / ".TRAINING_COMPLETE"
        completion_marker.touch()
        logger.info(f"\n[SUCCESS] Training complete! Marker created at {completion_marker}")

        return True

    except Exception as e:
        logger.error(f"\n[FAILED] Training pipeline failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    try:
        success = main()
        exit_code = 0 if success else 1
    except KeyboardInterrupt:
        logger.warning("\nTraining interrupted by user")
        exit_code = 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        exit_code = 1

    sys.exit(exit_code)
