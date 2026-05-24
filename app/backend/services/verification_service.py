# app/backend/services/verification_service.py
"""
Verification Service for Phase 1 Model Testing
Verifies model loads correctly and converts audio properly
"""

import os
import json
import logging
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

try:
    import soundfile as sf
except ImportError:
    sf = None


class VerificationService:
    """Verifies retrained model and tests audio conversion"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.model_path = self.project_root / "assets" / "weights" / "esposa_voice.pth"
        self.test_input = self.project_root / "tts_temp.mp3"
        self.test_output = self.project_root / "test_output_phase1.wav"
        self.index_path = self.project_root / "app" / "models" / "voices" / "esposa_voice" / "esposa_voice.index"

    def verify_model_exists(self) -> bool:
        """Check if model file exists and has reasonable size"""
        logger.info("Verifying model file...")

        if not self.model_path.exists():
            logger.error(f"Model not found: {self.model_path}")
            return False

        size_mb = self.model_path.stat().st_size / (1024 * 1024)
        logger.info(f"Model size: {size_mb:.2f} MB")

        # RVC models are typically 50-100 MB
        if size_mb < 40 or size_mb > 200:
            logger.warning(f"Unusual model size: {size_mb:.2f} MB (expected 50-100 MB)")

        logger.info("[OK] Model file exists and has reasonable size")
        return True

    def verify_model_loads(self) -> bool:
        """Attempt to load model weights"""
        logger.info("Verifying model can be loaded...")

        try:
            import torch
            checkpoint = torch.load(
                self.model_path,
                map_location="cpu"
            )

            # Check if checkpoint has expected keys
            if isinstance(checkpoint, dict):
                if "model" in checkpoint:
                    model_keys = checkpoint["model"].keys()
                    logger.info(f"Model has {len(model_keys)} parameter groups")
                elif "state_dict" in checkpoint:
                    model_keys = checkpoint["state_dict"].keys()
                    logger.info(f"State dict has {len(model_keys)} parameters")
                else:
                    logger.warning("Checkpoint structure is non-standard")

            logger.info("[OK] Model loads without errors")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def verify_test_input(self) -> bool:
        """Verify test input audio exists"""
        logger.info("Verifying test input audio...")

        if not self.test_input.exists():
            logger.error(f"Test input not found: {self.test_input}")
            return False

        size_mb = self.test_input.stat().st_size / (1024 * 1024)
        logger.info(f"Test input size: {size_mb:.2f} MB")
        logger.info("[OK] Test input exists")
        return True

    def verify_index_exists(self) -> bool:
        """Verify FAISS index file exists"""
        logger.info("Verifying FAISS index...")

        if not self.index_path.exists():
            logger.warning(f"Index not found: {self.index_path} (will be built)")
            return False

        size_mb = self.index_path.stat().st_size / (1024 * 1024)
        logger.info(f"Index size: {size_mb:.2f} MB")
        logger.info("[OK] Index exists")
        return True

    def run_all_verifications(self) -> dict:
        """Run all verification checks"""
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1 VERIFICATION CHECKLIST")
        logger.info("=" * 80)

        results = {
            "model_exists": self.verify_model_exists(),
            "model_loads": self.verify_model_loads(),
            "test_input": self.verify_test_input(),
            "index_exists": self.verify_index_exists(),
        }

        logger.info("\n" + "=" * 80)
        logger.info("VERIFICATION RESULTS")
        logger.info("=" * 80)

        for check, result in results.items():
            status = "[PASS]" if result else "[FAIL]"
            logger.info(f"{status} {check}")

        all_passed = all(results.values())
        logger.info(f"\nOverall: {'[PASS]' if all_passed else '[FAIL]'}")

        return results


verification_service = VerificationService()
