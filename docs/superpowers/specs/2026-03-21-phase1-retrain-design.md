# Phase 1: Fix & Retrain Voice Conversion Model

**Date:** 2026-03-21
**Status:** Design Approved
**Phase:** 1 of 3 (Voice Conversion Pipeline)

## Problem Statement

The `esposa_voice` RVC model is corrupted and produces a continuous 2.8kHz high-pitched square wave instead of natural speech. Root cause: Training used FP16 (half-precision) on CPU, which caused mathematical divergence in the neural network during training.

**Current State:**
- TTS generates robotic voice from text ✅
- RVC should convert robotic voice → wife's voice ❌ (produces noise)
- Web UI ready to serve conversions (waiting for working model)

## Solution Overview

Retrain the model with FP32 (full precision) on CPU. This fixes the precision errors and allows the model to learn the wife's voice correctly.

**Training Data:** `C:\Users\gaming\Desktop\dataset_alex\voice.wav` (14MB)
**Model Output:** `assets/weights/esposa_voice.pth`
**Duration:** ~2.5 hours (200 epochs, balanced approach)
**Execution:** Background mode with logging and auto-verification

## Architecture & Components

### 1. Configuration Fix

**File:** `configs/config.py` (or RVC training config location)

**Changes:**
```
BEFORE: fp16_run = True      →  AFTER: fp16_run = False
BEFORE: epochs = 300         →  AFTER: epochs = 200
```

**Why:**
- `fp16_run = False`: Forces FP32 (full precision), fixes CPU math errors
- `epochs = 200`: Balanced training (2.5 hours) instead of full 300 epochs
- Other parameters unchanged: Keep existing batch size, learning rate, etc.

### 2. Training Execution

**Execution Mode:** Background (non-blocking)

**Process:**
1. Apply config changes
2. Start RVC training script with `dataset_alex/voice.wav`
3. Redirect all output to `training_phase1.log` with timestamps
4. Training runs independently — terminal can be closed
5. Create `.TRAINING_COMPLETE` marker file when finished

**Monitoring:**
- Check progress anytime: `tail -f training_phase1.log`
- Expected duration: 2 hours 30 minutes on CPU
- Key metrics logged: epoch number, loss values (should decrease steadily)

### 3. Automatic Verification

**After training completes:**

**Step 1 - Model Validation:**
```
✓ Check model file exists: assets/weights/esposa_voice.pth
✓ Load model weights without errors
✓ Verify model architecture matches expected RVC v2 structure
```

**Step 2 - Audio Conversion Test:**
```
Input:  tts_temp.mp3 (robotic TTS voice, 507 characters of Portuguese text)
Model:  esposa_voice (newly trained)
Output: test_output_phase1.wav
```

**Step 3 - Quality Metrics:**
- Audio length matches input (no clipping)
- Volume normalized (no extreme peaks)
- WAV format valid and playable
- No NaN/Inf values in output

### 4. Success Criteria

**Verification passes when:**
- ✅ Model file loads without errors
- ✅ RVC conversion completes without crashes
- ✅ Output audio is generated: `test_output_phase1.wav`
- ✅ No 2.8kHz noise present (listening test)
- ✅ Audio sounds like natural speech (not robotic)
- ✅ Words are intelligible in Portuguese

**Manual Quality Check:**
User listens to `test_output_phase1.wav` and confirms:
- [ ] No high-pitched continuous noise
- [ ] Audio sounds like wife's voice
- [ ] Speech is clear and understandable
- [ ] Volume levels are normal

## Workflow

```
[1] FIX CONFIG
    └─ Set fp16_run = False, epochs = 200

[2] START TRAINING (Background)
    ├─ Dataset: dataset_alex/voice.wav (14MB)
    ├─ Logging: training_phase1.log
    ├─ Duration: 2.5 hours
    └─ Terminal can be closed

[3] WAIT FOR COMPLETION
    └─ Monitor: tail -f training_phase1.log
    └─ Completion marker: .TRAINING_COMPLETE

[4] AUTO-VERIFY
    ├─ Load model file
    ├─ Test with tts_temp.mp3
    ├─ Save output: test_output_phase1.wav
    └─ Report success/failure

[5] MANUAL QUALITY CHECK
    └─ Listen to test_output_phase1.wav
    └─ Confirm: no noise, sounds natural
    └─ Ready for Phase 2: HeyGen integration

[SUCCESS]
└─ Model ready for web UI and downstream processes
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Training fails immediately | Config not applied | Verify `fp16_run = False` in config file |
| Model loads but produces noise | FP32 not actually used | Check if config was saved correctly |
| Model file not found after training | Training didn't complete | Check `training_phase1.log` for errors |
| Conversion produces clipping/distortion | Loss didn't converge | May need to adjust learning rate and retrain |

## Files Modified/Created

**Modified:**
- `configs/config.py` - FP16 disabled, epochs reduced

**Created:**
- `training_phase1.log` - Training output and progress log
- `test_output_phase1.wav` - Verification audio output
- `.TRAINING_COMPLETE` - Marker file when done

**Existing (reused):**
- `dataset_alex/voice.wav` - Training data source
- `assets/weights/esposa_voice.pth` - Output model (overwrites old)
- `tts_temp.mp3` - Test input for verification

## Next Steps

After Phase 1 succeeds:
1. **Phase 2:** Integrate HeyGen API for video generation
2. **Phase 3:** Automatic video editing + social media scheduling

If Phase 1 fails:
1. Check logs for specific error
2. Adjust config (learning rate, batch size, etc.)
3. Retrain with adjusted settings

## Timeline

| Task | Duration | Start | End |
|------|----------|-------|-----|
| Config fix | 5 min | Now | Now + 5m |
| Training | 2.5 hours | Now + 5m | Now + 2h 35m |
| Verification | 5 min | Now + 2h 35m | Now + 2h 40m |
| Manual QA | 10 min | Now + 2h 40m | Now + 2h 50m |
| **Total** | **~2h 50m** | | |

## Success Definition

Phase 1 is complete when:
1. ✅ Model file exists and loads successfully
2. ✅ Conversion test produces clean audio (no 2.8kHz noise)
3. ✅ Audio sounds like wife's natural voice
4. ✅ Web UI can use the model for conversions
5. ✅ Ready to proceed to Phase 2 (HeyGen integration)
