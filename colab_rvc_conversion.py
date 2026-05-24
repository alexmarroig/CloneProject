"""
Google Colab RVC Voice Conversion Notebook
Copy and paste this code into a Colab cell

This script will:
1. Install RVC dependencies
2. Load your trained esposa_voice model
3. Convert your TTS audio to use your wife's voice
4. Download the result
"""

# ============================================================================
# CELL 1: Setup and Installations
# ============================================================================

# Install RVC and dependencies
!pip install -q torch torchvision torchaudio
!pip install -q fairseq
!pip install -q librosa soundfile numpy scipy
!pip install -q pydub

print("[OK] Dependencies installed")

# ============================================================================
# CELL 2: Upload Files
# ============================================================================

from google.colab import files
from pathlib import Path

print("="*70)
print("Upload your files:")
print("="*70)
print("\n1. Upload your trained model: esposa_voice.pth")
uploaded = files.upload()
model_file = list(uploaded.keys())[0]

print("\n2. Upload your TTS audio: tts_temp.mp3")
uploaded = files.upload()
audio_file = list(uploaded.keys())[0]

print(f"\n[OK] Files uploaded:")
print(f"  Model: {model_file}")
print(f"  Audio: {audio_file}")

# ============================================================================
# CELL 3: Clone RVC Repository
# ============================================================================

import os
os.chdir("/content")

# Clone RVC repository
!git clone -q https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git RVC
os.chdir("/content/RVC")

print("[OK] RVC cloned successfully")

# ============================================================================
# CELL 4: Copy Your Model
# ============================================================================

import shutil
from pathlib import Path

# Create weights directory
Path("assets/weights").mkdir(parents=True, exist_ok=True)

# Copy model to RVC directory
shutil.copy(f"/content/{model_file}", "assets/weights/esposa_voice.pth")
shutil.copy(f"/content/{audio_file}", audio_file)

print(f"[OK] Model copied to RVC weights directory")

# ============================================================================
# CELL 5: Run Voice Conversion
# ============================================================================

import sys
sys.path.insert(0, "/content/RVC")

from infer.modules.vc.modules import VC
import soundfile as sf
import librosa
import torch

print("="*70)
print("Starting Voice Conversion")
print("="*70)
print()

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Initialize VC
vc = VC(
    tgt_sr=40000,
    device=device,
    is_half=device == "cuda"
)

# Load model
print("\nLoading model: esposa_voice.pth")
vc.get_vc("esposa_voice.pth", 0, device)
print("[OK] Model loaded")

# Load audio
print(f"\nLoading audio: {audio_file}")
audio_data, sr = librosa.load(audio_file, sr=40000)
print(f"[OK] Audio loaded: {len(audio_data)} samples @ {sr}Hz")

# Convert voice
print("\nApplying voice conversion...")
output_audio, _ = vc.infer(
    speaker_id=0,
    audio_data=audio_data,
    times=0,
    top_k=5,
    top_p=1,
    temperature=1
)

output_audio = output_audio[0, 0].data.cpu().numpy() if isinstance(output_audio, torch.Tensor) else output_audio

# Normalize audio
if output_audio.max() > 0:
    output_audio = output_audio / output_audio.max() * 0.95

# Save output
output_file = "reels_audio_esposa_voice.wav"
sf.write(output_file, output_audio, sr)

print(f"\n[OK] Voice conversion complete!")
print(f"Output: {output_file}")
print(f"Duration: {len(output_audio) / sr:.2f} seconds")

# ============================================================================
# CELL 6: Download Result
# ============================================================================

print("\n" + "="*70)
print("Downloading your audio with wife's voice...")
print("="*70)
print()

files.download(output_file)

print(f"\n[SUCCESS] Download started!")
print(f"Your file: {output_file}")
print(f"Ready to use in your reels! [OK]")
