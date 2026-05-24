"""
Training Launcher
Starts training in background and monitors progress
"""

import subprocess
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TrainingLauncher:
    """Launches and monitors background training"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.log_file = self.project_root / "logs" / "training_phase1.log"

    def start_training(self) -> bool:
        """Start training in background"""
        logger.info("Starting background training...")

        script_path = self.project_root / "scripts" / "retrain_esposa_voice.py"

        if not script_path.exists():
            logger.error(f"Training script not found: {script_path}")
            return False

        try:
            # Start training in background
            # Windows: Use subprocess.Popen with CREATE_NEW_CONSOLE or without stdio
            # Unix: Use nohup or subprocess.Popen with stdout/stderr redirected

            if sys.platform == "win32":
                # Windows: Detach from current process
                process = subprocess.Popen(
                    [sys.executable, str(script_path)],
                    stdout=open(self.log_file, 'a'),
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    cwd=str(self.project_root),
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP') else 0
                )
            else:
                # Unix: Use nohup equivalent
                process = subprocess.Popen(
                    [sys.executable, str(script_path)],
                    stdout=open(self.log_file, 'a'),
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    cwd=str(self.project_root),
                    preexec_fn=None  # Disable signal inheritance
                )

            logger.info(f"Training started with PID: {process.pid}")
            logger.info(f"Logs: {self.log_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to start training: {e}")
            return False

    def check_log_file(self) -> str:
        """Get last 20 lines of log file"""
        if not self.log_file.exists():
            return "Log file not created yet"

        with open(self.log_file, 'r') as f:
            lines = f.readlines()

        return "".join(lines[-20:])


training_launcher = TrainingLauncher()
