import os
import sys
import torch
from pathlib import Path

# Add current directory to path for imports
now_dir = os.getcwd()
sys.path.append(now_dir)

from configs.config import Config
from infer.modules.vc.modules import VC
from scipy.io import wavfile

def main():
    print("="*70)
    print("RVC Inference - Optimized for Reels (RMVPE)")
    print("="*70)

    # Configuration
    model_name = "esposa_voice.pth"
    input_path = "reels_audio_esposa_voice.wav"
    output_path = "reels_audio_esposa_voice_rvc.wav"
    f0_method = "rmvpe" # Faster and better than harvest/pm
    
    # Set environment variables for RMVPE
    os.environ["weight_root"] = os.path.join(now_dir, "assets", "weights")
    os.environ["index_root"] = os.path.join(now_dir, "logs")
    os.environ["rmvpe_root"] = os.path.join(now_dir, "assets", "rmvpe")

    if not Path(input_path).exists():
        print(f"[ERROR] Input file not found: {input_path}")
        return

    print(f"Input: {input_path}")
    print(f"Model: {model_name}")
    print(f"Method: {f0_method}")
    print(f"Output: {output_path}")

    # Initialize RVC
    config = Config()
    config.device = "cpu" # Force CPU as per environment
    config.is_half = False # CPU doesn't support half well for some ops
    
    print("\n[1/3] Loading model...")
    vc = VC(config)
    vc.get_vc(model_name)
    
    print("\n[2/3] Converting voice (this may take 5-10 minutes on CPU)...")
    # vc_single returns (info, (tgt_sr, audio_opt))
    info, wav_opt = vc.vc_single(
        0,                 # sid
        input_path,        # input_audio_path
        0,                 # f0_up_key
        None,              # f0_file
        f0_method,         # f0_method
        "",                # file_index
        "",                # file_index2
        0.7,               # index_rate
        3,                 # filter_radius
        0,                 # resample_sr (0 = no resample)
        1.0,               # rms_mix_rate
        0.33,              # protect
    )
    
    if wav_opt[0] is None:
        print(f"\n[ERROR] Conversion failed: {info}")
        return

    print(f"\n[3/3] Saving output...")
    wavfile.write(output_path, wav_opt[0], wav_opt[1])
    
    print("\n" + "="*70)
    print("[SUCCESS] Voice conversion complete!")
    print(f"Result: {Path(output_path).absolute()}")
    print("="*70)

if __name__ == "__main__":
    main()
