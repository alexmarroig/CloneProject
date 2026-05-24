"""
Clean RVC training pipeline for esposa_voice.
Uses ONLY the wife's original audio recording.
Runs preprocessing, feature extraction, and training with proper timeout.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path.cwd()
VOICE_NAME = "esposa_voice"
SR = 40000
SR_KEY = "40k"
VERSION = "v2"
EPOCHS = 200
BATCH_SIZE = 1

# Step 0: Create a clean dataset folder with ONLY the wife's voice
print("=" * 70)
print("[0/5] CREATING CLEAN DATASET")
print("=" * 70)

clean_dataset = PROJECT_ROOT / "dataset_esposa_clean"
if clean_dataset.exists():
    shutil.rmtree(clean_dataset)
clean_dataset.mkdir()

# Copy ONLY the original recording
src = PROJECT_ROOT / "app" / "runtime" / "datasets" / "esposa_original.wav"
if not src.exists():
    src = Path(r"C:\Users\gaming\Desktop\dataset_alex\voice.wav")
dst = clean_dataset / "esposa_original.wav"
shutil.copy2(src, dst)
print(f"Copied: {src.name} -> {dst}")
print(f"Dataset: 1 file, {dst.stat().st_size / 1024 / 1024:.1f} MB")

# Step 1: Clean old training data
print("\n" + "=" * 70)
print("[1/5] CLEANING OLD TRAINING DATA")
print("=" * 70)

logs_dir = PROJECT_ROOT / "logs" / VOICE_NAME
if logs_dir.exists():
    shutil.rmtree(logs_dir, ignore_errors=True)
    print(f"Removed: {logs_dir}")

# Also remove the old preprocessing output
old_preproc = PROJECT_ROOT / VOICE_NAME
if old_preproc.exists():
    shutil.rmtree(old_preproc, ignore_errors=True)
    print(f"Removed: {old_preproc}")

# Step 2: Preprocess audio
print("\n" + "=" * 70)
print("[2/5] PREPROCESSING - Slicing and resampling audio")
print("=" * 70)

cmd = [
    sys.executable,
    "infer/modules/train/preprocess.py",
    str(clean_dataset),  # Input directory (clean, only wife's voice)
    str(SR),             # Sample rate
    "2",                 # Number of processes
    VOICE_NAME,          # Experiment name
    "False",             # No parallel
    "3.0",               # Minimum seconds per slice
]
print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
if result.returncode != 0:
    print("[ERROR] Preprocessing failed!")
    sys.exit(1)
print("[OK] Preprocessing done")

# Step 3: Extract F0 (pitch)
print("\n" + "=" * 70)
print("[3/5] EXTRACTING F0 (PITCH)")
print("=" * 70)

cmd = [
    sys.executable,
    "infer/modules/train/extract/extract_f0_print.py",
    VOICE_NAME,  # Experiment name
    "2",         # Number of processes
    "rmvpe",     # F0 method
]
print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
if result.returncode != 0:
    print("[ERROR] F0 extraction failed!")
    sys.exit(1)
print("[OK] F0 extraction done")

# Step 4: Extract Hubert features
print("\n" + "=" * 70)
print("[4/5] EXTRACTING HUBERT FEATURES")
print("=" * 70)

cmd = [
    sys.executable,
    "infer/modules/train/extract_feature_print.py",
    "cpu",       # Device
    "1",         # Number of parts
    "0",         # Part index
    VOICE_NAME,  # Experiment name
    VERSION,     # Version
    "False",     # is_half (MUST be False for CPU!)
]
print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
if result.returncode != 0:
    print("[ERROR] Feature extraction failed!")
    sys.exit(1)
print("[OK] Feature extraction done")

# Move processed data to logs directory
src_dir = PROJECT_ROOT / VOICE_NAME
logs_dir = PROJECT_ROOT / "logs" / VOICE_NAME
if src_dir.exists() and not logs_dir.exists():
    shutil.move(str(src_dir), str(logs_dir))
    print(f"Moved {src_dir} -> {logs_dir}")

# Generate filelist and copy config
print("\nGenerating filelist...")
gt_dir = logs_dir / "0_gt_wavs"
f0_dir = logs_dir / "2a_f0"
f0nsf_dir = logs_dir / "2b-f0nsf"
feat_dir = logs_dir / "3_feature768"

# Copy config  
config_src = PROJECT_ROOT / "configs" / VERSION / f"{SR_KEY}.json"
config_dst = logs_dir / "config.json"
shutil.copyfile(config_src, config_dst)
print(f"Config copied: {config_dst}")

# Build filelist
opt = []
for name in os.listdir(gt_dir):
    if not name.endswith(".wav"):
        continue
    base = name.split(".")[0]
    p_gt = str(gt_dir / f"{base}.wav").replace("\\", "/")
    p_feat = str(feat_dir / f"{base}.npy").replace("\\", "/")
    p_f0 = str(f0_dir / f"{base}.wav.npy").replace("\\", "/")
    p_f0nsf = str(f0nsf_dir / f"{base}.wav.npy").replace("\\", "/")
    if all(os.path.exists(p) for p in [p_gt, p_feat, p_f0, p_f0nsf]):
        opt.append(f"{p_gt}|{p_feat}|{p_f0}|{p_f0nsf}|0")

# Add mute sample
mute_dir = PROJECT_ROOT / "logs" / "mute"
mute_gt = str(mute_dir / "0_gt_wavs" / f"mute{SR_KEY}.wav").replace("\\", "/")
mute_feat = str(mute_dir / "3_feature768" / "mute.npy").replace("\\", "/")
mute_f0 = str(mute_dir / "2a_f0" / "mute.wav.npy").replace("\\", "/")
mute_f0nsf = str(mute_dir / "2b-f0nsf" / "mute.wav.npy").replace("\\", "/")
if os.path.exists(mute_gt):
    opt.append(f"{mute_gt}|{mute_feat}|{mute_f0}|{mute_f0nsf}|0")

filelist_path = logs_dir / "filelist.txt"
with open(filelist_path, "w", encoding="utf-8") as f:
    f.write("\n".join(opt))
print(f"Filelist: {len(opt)} entries -> {filelist_path}")

# Step 5: Train!
print("\n" + "=" * 70)
print(f"[5/5] TRAINING - {EPOCHS} epochs on CPU (this will take several hours)")
print("=" * 70)
print("The model will save checkpoints every 10 epochs.")
print("You can safely close this window and the training will continue.")
print("Check logs/esposa_voice/train.log for progress.\n")

# Use pretrained models for faster convergence
pretrain_g = str(PROJECT_ROOT / "assets" / "pretrained_v2" / f"f0G{SR_KEY}.pth")
pretrain_d = str(PROJECT_ROOT / "assets" / "pretrained_v2" / f"f0D{SR_KEY}.pth")

cmd = [
    sys.executable,
    str(PROJECT_ROOT / "infer" / "modules" / "train" / "train.py"),
    "-se", "10",             # Save every 10 epochs
    "-te", str(EPOCHS),      # Total epochs
    "-bs", str(BATCH_SIZE),  # Batch size
    "-e", VOICE_NAME,        # Experiment name
    "-sr", SR_KEY,           # Sample rate
    "-v", VERSION,           # Version
    "-f0", "1",              # Use F0
    "-l", "0",               # Don't load latest (start fresh)
    "-c", "0",               # Don't cache in GPU
    "-sw", "1",              # Save weights to assets/weights
]

# Add pretrained models if they exist
if os.path.exists(pretrain_g):
    cmd.extend(["-pg", pretrain_g])
    print(f"Using pretrained G: {pretrain_g}")
if os.path.exists(pretrain_d):
    cmd.extend(["-pd", pretrain_d])
    print(f"Using pretrained D: {pretrain_d}")

print(f"\nCommand: {' '.join(cmd)}\n")

# NO TIMEOUT - let it run as long as needed
result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
print(f"\nTraining finished with exit code: {result.returncode}")

if result.returncode == 0:
    print("\n" + "=" * 70)
    print("SUCCESS! Training complete!")
    print("=" * 70)
else:
    print("\n[WARNING] Training may have ended early. Check the logs.")

# Check what was saved
import glob
weights = glob.glob(str(PROJECT_ROOT / "assets" / "weights" / "esposa_voice*.pth"))
checkpoints = glob.glob(str(logs_dir / "G_*.pth"))
print(f"\nSaved weights: {len(weights)}")
for w in weights:
    print(f"  {w} ({os.path.getsize(w)/1024/1024:.1f} MB)")
print(f"Saved checkpoints: {len(checkpoints)}")
for c in checkpoints:
    print(f"  {c} ({os.path.getsize(c)/1024/1024:.1f} MB)")
