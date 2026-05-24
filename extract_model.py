"""
Extract a usable RVC model from training checkpoint using extract_small_model.
"""
import os
import sys
sys.path.append(os.getcwd())

from infer.lib.train.process_ckpt import extract_small_model

# Use the latest checkpoint
checkpoint_path = "logs/esposa_voice/G_2610.pth"
model_name = "esposa_voice"
sr = "40k"
if_f0 = 1
info = "esposa_voice trained 30 epochs FP32 CPU"
version = "v2"

print(f"Extracting model from: {checkpoint_path}")
result = extract_small_model(checkpoint_path, model_name, sr, if_f0, info, version)
print(f"Result: {result}")

# Verify
import torch
model_path = f"assets/weights/{model_name}.pth"
if os.path.exists(model_path):
    size_mb = os.path.getsize(model_path) / (1024 * 1024)
    print(f"Model saved: {model_path} ({size_mb:.1f} MB)")
else:
    print(f"ERROR: Model not found at {model_path}")
