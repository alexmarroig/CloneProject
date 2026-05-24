# RVC Model Training Guide - Web UI Edition

## Overview

This guide walks you through training a custom RVC (Retrieval-based Voice Conversion) model with your wife's voice using the web interface.

## Prerequisites

Before starting, ensure you have:

1. **Voice Recordings**: 30 seconds to 5 minutes of clear audio
   - Use the voice preparation script to validate quality:
     ```bash
     python prepare_voice_data.py --guide
     python prepare_voice_data.py --input <your_voice_files_directory>
     ```

2. **Services Running**:
   - XTTS Docker container (text-to-speech)
   - FastAPI backend (training interface)
   - RVC environment (voice conversion)

## Quick Start

### 1. Prepare Your Voice Data

**Option A: Use Command Line**
```bash
# Show recording guide
python prepare_voice_data.py --guide

# Validate your recorded voice files
python prepare_voice_data.py --input path/to/your/voice/files

# Save validation report
python prepare_voice_data.py --input path/to/your/voice/files --export report.json
```

**Option B: Prepare Files Directly**

1. Create folder: `app/runtime/datasets/esposa_voice/`
2. Copy your voice files (WAV, MP3, FLAC, M4A) into this folder
3. Name them clearly:
   - `wife_voice_01.wav`
   - `wife_voice_02.wav`
   - etc.

### 2. Start the Services

**Step 1: Start XTTS Docker Container**

```bash
# Make sure Docker is running, then start XTTS
docker run -it --rm -p 8001:5000 coqui/xtts:latest-cpu
# Or if you have CUDA: docker run -it --rm --gpus all -p 8001:5000 coqui/xtts:latest
```

Wait for:
```
2026-03-18 XX:XX:XX | INFO | TTS is ready
```

**Step 2: Start FastAPI Backend** (new terminal)

```bash
cd C:\Users\gaming\Desktop\Projetos\AI\Retrieval-based-Voice-Conversion-WebUI

# Activate the main Python environment
python -m venv venv  # if not already created
.\venv\Scripts\activate

# Install/update dependencies
pip install fastapi uvicorn

# Start the backend
python app/backend/api/main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:3000
```

**Step 3: Access Web Interface**

Open your browser and go to:
```
http://localhost:3000
```

### 3. Upload Voice Data

1. **Navigate to Dataset Section**
   - Click on "Datasets" or "Voice Training"
   - Look for upload button or "Add Dataset"

2. **Upload Your Voice Files**
   - Click "Upload Files"
   - Select your voice recordings (WAV files preferred)
   - Set dataset name: `esposa_voice` (or your chosen name)
   - Click Upload

3. **Verify Upload**
   - You should see the files listed
   - Check file sizes and properties

### 4. Validate Dataset

1. **Click "Validate Dataset"**
   - Select your uploaded dataset
   - System will check:
     - Audio duration and quality
     - File formats
     - Silence levels
     - Speech characteristics

2. **Review Validation Results**
   - Green checkmarks = ready to proceed
   - Yellow warnings = may work, but not ideal
   - Red errors = fix and reupload

3. **Minimum Requirements**
   - Total duration: 10+ seconds (30+ seconds recommended)
   - Audio quality: Clear speech without heavy background noise
   - File format: WAV, MP3, FLAC, or M4A
   - All files must be valid audio

### 5. Prepare Dataset

1. **Click "Prepare Dataset"**
   - Select your validated dataset
   - Toggle options:
     - ✓ Silence Trimming: ON (removes quiet sections)
     - ✓ Normalization: ON (balances audio levels)
     - ✓ Auto Segmentation: ON (splits into training chunks)
   - Segment length: 12 seconds (leave default)

2. **Wait for Preparation**
   - Status will show progress
   - This may take 1-5 minutes
   - System logs into: `logs/esposa_voice/`

3. **View Results**
   - Check prepared dataset statistics
   - Verify number of audio segments created
   - Total duration should match or be slightly less (after trimming)

### 6. Train RVC Model

1. **Navigate to "Train Voice" Section**

2. **Select Training Parameters**
   - Voice Name: `esposa_voice` (must match your dataset)
   - Dataset Name: Your uploaded dataset
   - Sample Rate: `40k` (recommended for wife's voice)
   - RVC Version: `v2` (latest, recommended)
   - Epochs: `300` (standard)
   - Batch Size: `1` (for CPU training)
   - Learning Rate: `0.0001` (standard)
   - Save Every N Epochs: `10` (save checkpoints)
   - Mixed Precision: OFF (not supported on CPU)
   - GPU Device: `auto` or `cpu`

3. **Start Training**
   - Click "Start Training"
   - System will show:
     - Current epoch number
     - Loss values
     - Estimated time remaining
   - Status updates every 30 seconds

4. **Monitor Training Progress**
   - Open "Jobs" section to see training status
   - Check logs: `logs/esposa_voice/train.log`
   - Look for loss values decreasing (good sign)

5. **Wait for Completion**
   - Training time: 30-90 minutes (depending on CPU and data size)
   - Don't close browser or terminal
   - System will build FAISS index automatically after training

### 7. Verify Model

1. **Check Model Files**
   ```
   assets/weights/esposa_voice/
   ├── esposa_voice.pth         (trained model, ~50-100MB)
   └── esposa_voice.index       (FAISS index, ~10-50MB)
   ```

2. **View Training Metrics**
   - Open training logs: `logs/esposa_voice/train.log`
   - Check final loss value
   - Verify model saved successfully

3. **List Available Models**
   - In web UI, click "Models" or "Voices"
   - You should see `esposa_voice` listed

### 8. Test the Model

1. **Generate Test Audio**
   - In "Generate Voice" section:
   - Select voice: `esposa_voice`
   - Enter test text: "Oi, esse é um teste da minha voz clonada"
   - Click Generate

2. **Listen to Output**
   - Download generated audio
   - Compare with original wife's voice
   - Check if conversion quality is acceptable

3. **Troubleshoot if Needed**
   - If output is distorted: Retrain with adjusted learning rate
   - If output doesn't sound like wife's voice: Retrain with different data
   - If training failed: Check logs for error messages

### 9. Use the Model

Once trained and tested:

1. **Convert Voice in Audio**
   ```
   POST /convert_voice
   {
       "voice": "esposa_voice",
       "input_path": "path/to/audio.wav",
       "pitch_shift": 0,
       "index_rate": 0.66
   }
   ```

2. **Generate Speech with Voice**
   ```
   POST /generate_voice
   {
       "voice": "esposa_voice",
       "text": "Your text here",
       "language": "pt"
   }
   ```

## Troubleshooting

### Training is Stuck

- Check if XTTS container is still running: `docker ps`
- Check logs: `logs/esposa_voice/train.log`
- Try restarting backend: Stop and restart `python app/backend/api/main.py`

### Model Produces Constant Tone

- **Cause**: Training data too short or poor quality
- **Fix**: Record more diverse voice samples (2-5 minutes)
- **Retrain**: Delete old model and retrain with better data

### Out of Memory Error

- Reduce batch size (already set to 1)
- Close other applications
- Use a machine with more RAM (8GB minimum recommended)

### Model Not Found

- Verify name matches exactly: `esposa_voice`
- Check model files exist in `assets/weights/esposa_voice/`
- Clear browser cache if using web UI

### Poor Voice Conversion Quality

- Retrain with more data (30+ seconds minimum)
- Use more diverse content and emotions
- Ensure training data is clear and noise-free
- Try different epochs or learning rate

## Training Times

| Data Duration | CPU | GPU |
|---------------|-----|-----|
| 10 seconds    | 20-30 min | 3-5 min |
| 30 seconds    | 40-60 min | 8-10 min |
| 1 minute      | 60-90 min | 15-20 min |
| 5 minutes     | 120-180 min | 30-45 min |

## Next Steps

After successful training:

1. **Use for voice cloning**: Generate speech with your wife's voice
2. **Voice conversion**: Convert any audio to your wife's voice
3. **Fine-tune**: Retrain with more data if needed
4. **Export**: Backup model in `assets/weights/esposa_voice/`

## Support

If training fails:
1. Check the error logs in `logs/esposa_voice/`
2. Verify voice data quality using `prepare_voice_data.py`
3. Ensure all services (Docker, backend, RVC) are running
4. Check system resources (RAM, CPU, disk space)

---

**Happy Training! Your wife's voice model will be ready soon!** 🎤🎵
