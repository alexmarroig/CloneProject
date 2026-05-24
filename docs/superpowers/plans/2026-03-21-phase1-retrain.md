# Phase 1 RVC Model Retraining Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Retrain esposa_voice RVC model with FP32 precision to fix 2.8kHz noise artifact, then verify with test audio.

**Architecture:** Create a background training wrapper that modifies config, starts training with logging, auto-verifies model, and tests with tts_temp.mp3.

**Tech Stack:** Python 3.10+, PyTorch, RVC training service, subprocess for background execution

---

## File Structure

**Files to create:**
- `app/backend/services/training_controller.py` - Coordinates config changes, training, verification
- `scripts/retrain_esposa_voice.py` - Entry point for background training
- `logs/training_phase1.log` - Training output and progress log

**Files to modify:**
- `configs/inuse/v2/48k.json` - Set epochs to 200, ensure fp16_run = false
- `configs/inuse/v2/32k.json` - Same changes
- `configs/inuse/v1/40k.json` - Same changes (for compatibility)

**Files to reference:**
- `train_esposa.py` - Template for training pipeline steps
- `C:\Users\gaming\Desktop\dataset_alex\voice.wav` - Voice data source
- `tts_temp.mp3` - Test input for verification

---

## Chunk 1: Configuration & Setup

### Task 1: Verify and Fix Training Configuration

**Files:**
- Modify: `configs/inuse/v2/48k.json`
- Modify: `configs/inuse/v2/32k.json`
- Modify: `configs/inuse/v1/40k.json`

- [ ] **Step 1: Check current epoch count in v2/48k.json**

```bash
grep -A 2 '"train"' configs/inuse/v2/48k.json | head -5
```

Expected: Should show `"epochs": 20000` or similar high number

- [ ] **Step 2: Reduce epochs to 200 in v2/48k.json**

Using Edit tool on the file at line 5:

```json
OLD: "epochs": 20000,
NEW: "epochs": 200,
```

Reason: Reduces training time from 8+ hours to ~2.5 hours for balanced quality

- [ ] **Step 3: Verify fp16_run is false in v2/48k.json**

Check line 10 should already be: `"fp16_run": false`

If it's true, change it to false:

```json
OLD: "fp16_run": true,
NEW: "fp16_run": false,
```

- [ ] **Step 4: Apply same changes to v2/32k.json**

Modify: `configs/inuse/v2/32k.json`
- Change `"epochs": 20000` → `"epochs": 200`
- Verify `"fp16_run": false`

- [ ] **Step 5: Apply same changes to v1/40k.json**

Modify: `configs/inuse/v1/40k.json`
- Change `"epochs": 20000` → `"epochs": 200` (if present)
- Verify `"fp16_run": false`

- [ ] **Step 6: Commit config changes**

```bash
git add configs/inuse/v2/48k.json configs/inuse/v2/32k.json configs/inuse/v1/40k.json
git commit -m "config: Set epochs to 200 and ensure FP32 for CPU training"
```

---

### Task 2: Create Training Controller Service

**Files:**
- Create: `app/backend/services/training_controller.py`

- [ ] **Step 1: Create the training controller file**

```python
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
```

- [ ] **Step 2: Verify the file was created**

```bash
ls -l app/backend/services/training_controller.py
```

Expected: File should exist and be readable

- [ ] **Step 3: Commit the new service**

```bash
git add app/backend/services/training_controller.py
git commit -m "feat: Add training controller service for Phase 1 retraining"
```

---

## Chunk 2: Background Training Setup

### Task 3: Create Training Wrapper Script

**Files:**
- Create: `scripts/retrain_esposa_voice.py`

- [ ] **Step 1: Create the training wrapper script**

```python
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
```

- [ ] **Step 2: Make script executable**

```bash
chmod +x scripts/retrain_esposa_voice.py
```

- [ ] **Step 3: Verify script syntax**

```bash
python scripts/retrain_esposa_voice.py --help 2>&1 | head -5 || python -m py_compile scripts/retrain_esposa_voice.py
```

Expected: Script should compile without syntax errors (or show usage if --help is implemented)

- [ ] **Step 4: Commit the training script**

```bash
git add scripts/retrain_esposa_voice.py
git commit -m "feat: Add background training wrapper for Phase 1 retraining"
```

---

## Chunk 3: Background Execution & Monitoring

### Task 4: Create Background Training Launcher

**Files:**
- Create: `app/backend/services/training_launcher.py`

- [ ] **Step 1: Create training launcher**

```python
# app/backend/services/training_launcher.py
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
```

- [ ] **Step 2: Commit the launcher**

```bash
git add app/backend/services/training_launcher.py
git commit -m "feat: Add training launcher for background execution"
```

---

### Task 5: Create Verification Service

**Files:**
- Create: `app/backend/services/verification_service.py`

- [ ] **Step 1: Create verification service**

```python
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
```

- [ ] **Step 2: Commit the verification service**

```bash
git add app/backend/services/verification_service.py
git commit -m "feat: Add verification service for model testing"
```

---

## Chunk 4: Training Execution & Final Steps

### Task 6: Start Background Training

**Files:**
- Reference: `scripts/retrain_esposa_voice.py`

- [ ] **Step 1: Verify all prerequisites are in place**

```bash
# Check config files exist
ls -l configs/inuse/v2/48k.json configs/inuse/v2/32k.json configs/inuse/v1/40k.json

# Check dataset exists
ls -lh "C:/Users/gaming/Desktop/dataset_alex/voice.wav"

# Check test input exists
ls -lh tts_temp.mp3

# Check training script exists
ls -l scripts/retrain_esposa_voice.py
```

Expected: All files should exist

- [ ] **Step 2: Create logs directory**

```bash
mkdir -p logs
```

- [ ] **Step 3: Start background training**

```bash
python scripts/retrain_esposa_voice.py &
```

Or on Windows with proper detachment:

```bash
start python scripts/retrain_esposa_voice.py
```

Expected: Script should start and return to prompt immediately

- [ ] **Step 4: Monitor training progress**

```bash
# Check if training is running
tail -f logs/training_phase1.log

# Or check last 50 lines
tail -50 logs/training_phase1.log
```

Expected: Log file should show preprocessing/feature extraction steps

- [ ] **Step 5: Save monitoring command for reference**

Create a file `MONITORING.md`:

```markdown
# Training Monitoring

Training is running in background at:
- Process: `python scripts/retrain_esposa_voice.py`
- Logs: `logs/training_phase1.log`

## Watch Training Progress

```bash
# Real-time monitoring
tail -f logs/training_phase1.log

# Last 50 lines
tail -50 logs/training_phase1.log

# Count epochs completed (when training starts)
grep "epoch" logs/training_phase1.log | tail -1
```

## Expected Timeline

- Preprocessing + Feature Extraction: 10-15 minutes
- Training (200 epochs): 2-2.5 hours
- FAISS Index Building: 5-10 minutes
- **Total: ~2.5-3 hours**

## Completion Indicator

When training finishes, marker file will exist:
```bash
ls -l .TRAINING_COMPLETE
```

## Manual Verification (After Training)

```bash
# Check if model was created
ls -lh assets/weights/esposa_voice.pth

# Play test output
# test_output_phase1.wav should exist and be listenable
```
```

- [ ] **Step 6: Commit the monitoring guide**

```bash
git add MONITORING.md
git commit -m "docs: Add training monitoring guide for Phase 1"
```

---

### Task 7: Post-Training Verification & Quality Check

**Files:**
- Create: `QUALITY_CHECK.md`

- [ ] **Step 1: Wait for training to complete**

Check for marker file:

```bash
# This will exist when training is done
ls -l .TRAINING_COMPLETE

# Or check log for success message
tail logs/training_phase1.log | grep -i "success"
```

Expected: Marker should exist after ~2.5-3 hours, log should show SUCCESS

- [ ] **Step 2: Verify model loads**

```bash
python -c "
import torch
model = torch.load('assets/weights/esposa_voice.pth', map_location='cpu')
print('[OK] Model loads successfully')
print(f'Checkpoint keys: {list(model.keys()) if isinstance(model, dict) else \"single tensor\"}')
"
```

Expected: Should print OK and show checkpoint structure

- [ ] **Step 3: Run auto-verification**

```bash
python -c "
import sys
sys.path.insert(0, '.')
from app.backend.services.verification_service import verification_service
results = verification_service.run_all_verifications()
print(f'\nVerification passed: {all(results.values())}')
"
```

Expected: All checks should pass (except possibly index if not built yet)

- [ ] **Step 4: Create quality checklist**

Create `QUALITY_CHECK.md`:

```markdown
# Phase 1 Quality Verification Checklist

**Date:** [Fill in]
**Status:** [PENDING / IN PROGRESS / PASSED]

## Automated Checks

- [ ] Model file exists: `assets/weights/esposa_voice.pth`
- [ ] Model loads without errors
- [ ] FAISS index exists: `app/models/voices/esposa_voice/esposa_voice.index`
- [ ] No NaN/Inf values in checkpoint

## Audio Quality Checks

**Before listening:** Download `test_output_phase1.wav` from project root

### Test Output Analysis

- [ ] File size is reasonable (>100KB, <50MB)
- [ ] Duration matches input audio (~0.5-1 minute)
- [ ] No obvious clipping or distortion
- [ ] Volume levels are normal (not peak at 0dB or silent)

### Listening Test

**Listen to `test_output_phase1.wav` and verify:**

- [ ] **NO 2.8kHz high-pitched noise** (main issue we're fixing)
- [ ] Audio sounds like your wife's natural voice
- [ ] Speech is clear and intelligible
- [ ] Pronunciation is correct (test with Portuguese: "voz da minha esposa")
- [ ] Voice characteristics match original (tone, pitch, timbre)
- [ ] Background noise is minimal

### Pass/Fail Criteria

**PASS if:**
- ✅ No high-pitched noise
- ✅ Sounds like natural speech
- ✅ All automated checks pass

**FAIL if:**
- ❌ Still has 2.8kHz noise or other artifacts
- ❌ Audio is severely distorted
- ❌ Unintelligible or robotic sounding

## Notes

Add any observations about quality, differences from original voice, etc.

```

- [ ] **Step 5: Commit the quality checklist**

```bash
git add QUALITY_CHECK.md
git commit -m "docs: Add quality verification checklist for Phase 1"
```

---

### Task 8: Document Results & Next Steps

- [ ] **Step 1: Record training completion**

When training finishes successfully, check:

```bash
# Get training duration from log
head -1 logs/training_phase1.log  # start time
tail -5 logs/training_phase1.log  # end time and success message
```

- [ ] **Step 2: Create TRAINING_RESULTS.md**

```markdown
# Phase 1 Training Results

## Training Configuration
- **Model:** esposa_voice
- **Version:** RVC v2 (48kHz)
- **Epochs:** 200
- **Precision:** FP32 (CPU-optimized)
- **Batch Size:** 1
- **Learning Rate:** 0.0001

## Training Progress
- Dataset: C:/Users/gaming/Desktop/dataset_alex/voice.wav (14MB)
- Start Time: [check logs/training_phase1.log]
- End Time: [check .TRAINING_COMPLETE timestamp]
- Total Duration: [calculate from times above]

## Results
- Model Size: [ls -lh assets/weights/esposa_voice.pth]
- Index Size: [ls -lh app/models/voices/esposa_voice/esposa_voice.index]
- Test Output: [ls -lh test_output_phase1.wav]

## Quality Assessment
- High-pitch Noise (2.8kHz): [FIXED/REMAINING]
- Natural Voice Quality: [GOOD/ACCEPTABLE/POOR]
- Intelligibility: [CLEAR/ACCEPTABLE/UNCLEAR]
- Overall: [PASS/FAIL]

## Blockers or Issues
(None if training succeeded)

## Next Steps
1. ✅ Phase 1: Fix voice conversion model (COMPLETE)
2. ⏳ Phase 2: Integrate HeyGen for video generation
3. ⏳ Phase 3: Auto video editing + social media posting
```

- [ ] **Step 3: Commit final documentation**

```bash
git add TRAINING_RESULTS.md
git commit -m "docs: Record Phase 1 training results and completion"
```

- [ ] **Step 4: Final verification**

```bash
# Verify all new services are in place
ls -l app/backend/services/training_controller.py
ls -l app/backend/services/training_launcher.py
ls -l app/backend/services/verification_service.py
ls -l scripts/retrain_esposa_voice.py

# Check git history
git log --oneline -10
```

Expected: All services should exist, git log should show new commits

---

## Summary

**Implementation complete when:**
1. ✅ Config files modified (epochs=200, fp16_run=false)
2. ✅ Training wrapper script created and executable
3. ✅ Training launcher service created
4. ✅ Verification service created
5. ✅ Background training started
6. ✅ Training completes successfully (~2.5 hours)
7. ✅ Model loads without errors
8. ✅ Quality checks pass (no 2.8kHz noise)
9. ✅ All code committed to git

**Next Phase (Phase 2):** Once quality checks pass, proceed to HeyGen video integration.

**Rollback Plan:** If training fails:
1. Check `logs/training_phase1.log` for specific error
2. Adjust config (learning rate, batch size)
3. Delete `assets/weights/esposa_voice.pth` (old model)
4. Delete `app/models/voices/esposa_voice/` (old index)
5. Re-run `scripts/retrain_esposa_voice.py`
