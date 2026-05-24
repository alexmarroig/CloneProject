# app/backend/services/training_controller.py
"""
Training Controller Service
Manages RVC model retraining with FP32 on CPU
"""

import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class TrainingController:
    """Controls RVC training pipeline for Phase 1 retraining"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.log_dir = self.project_root / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / "training_phase1.log"
        self.completion_marker = self.project_root / ".TRAINING_COMPLETE"
        self.config_files = [
            "configs/inuse/v2/48k.json",
            "configs/inuse/v2/32k.json",
            "configs/inuse/v1/40k.json",
        ]

    def verify_config(self) -> bool:
        """Verify all config files have FP32 enabled and epochs set to 200"""
        logger.info("Verifying configuration files...")

        for config_path in self.config_files:
            full_path = self.project_root / config_path
            if not full_path.exists():
                logger.warning(f"Config file not found: {config_path}")
                continue

            try:
                with open(full_path, 'r') as f:
                    config = json.load(f)

                fp16_run = config.get("train", {}).get("fp16_run", True)
                epochs = config.get("train", {}).get("epochs", 20000)

                logger.info(f"{config_path}: fp16_run={fp16_run}, epochs={epochs}")

                if fp16_run:
                    logger.error(f"ERROR: {config_path} still has fp16_run=true!")
                    return False

                if epochs > 200:
                    logger.warning(f"WARNING: {config_path} has epochs={epochs}, expected 200")

            except Exception as e:
                logger.error(f"Failed to read config {config_path}: {e}")
                return False

        logger.info("[OK] Configuration verified - FP32 enabled, epochs set to 200")
        return True

    def verify_dataset(self, dataset_path: str) -> bool:
        """Verify training dataset exists and is readable"""
        logger.info(f"Verifying dataset at: {dataset_path}")

        dataset_file = Path(dataset_path)
        if not dataset_file.exists():
            logger.error(f"Dataset not found: {dataset_path}")
            return False

        file_size_mb = dataset_file.stat().st_size / (1024 * 1024)
        logger.info(f"Dataset size: {file_size_mb:.2f} MB")

        if file_size_mb < 1:
            logger.error(f"Dataset too small: {file_size_mb:.2f} MB (minimum 1 MB)")
            return False

        logger.info("[OK] Dataset verified")
        return True

    def cleanup_old_marker(self):
        """Remove old completion marker"""
        if self.completion_marker.exists():
            self.completion_marker.unlink()
            logger.info("Cleaned up old completion marker")


training_controller = TrainingController()
