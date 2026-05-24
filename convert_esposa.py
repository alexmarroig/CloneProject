import os
import sys
import torch
from pathlib import Path

# Add project root to sys.path
now_dir = os.getcwd()
sys.path.append(now_dir)

from configs.config import Config
from infer.modules.vc.modules import VC

def run_conversion(input_path, output_path, model_name):
    print(f"Starting conversion for: {input_path}")
    print(f"Using model: {model_name}")
    
    # Initialize Config and VC
    # Note: Config() is a singleton in this project's implementation
    config = Config()
    vc = VC(config)
    
    # Check if model exists
    model_path = os.path.join("assets", "weights", model_name)
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        return False
        
    # Load the model
    # get_vc returns (spk_id_update, protect0_update, protect1_update, index_update, index_update_2)
    # but more importantly it sets up self.net_g and self.pipeline
    vc.get_vc(model_name)
    
    # Conversion parameters
    sid = 0 # Speaker ID
    f0_up_key = 0 # Pitch (0 = no change)
    f0_file = None
    f0_method = "rmvpe" # High quality pitch extraction
    file_index = "" # We'll try without index first, or find one if available
    file_index2 = ""
    index_rate = 0.75
    filter_radius = 3
    resample_sr = 0 # No resampling
    rms_mix_rate = 0.25
    protect = 0.33
    
    # Try to find an index file for this model
    index_dir = os.path.join("logs", model_name.split(".")[0])
    if os.path.exists(index_dir):
        for f in os.listdir(index_dir):
            if f.endswith(".index") and "added" in f:
                file_index = os.path.join(index_dir, f)
                print(f"Found index file: {file_index}")
                break

    # Run conversion
    info, (tgt_sr, audio_opt) = vc.vc_single(
        sid,
        input_path,
        f0_up_key,
        f0_file,
        f0_method,
        file_index,
        file_index2,
        index_rate,
        filter_radius,
        resample_sr,
        rms_mix_rate,
        protect
    )
    
    if "Success" in info:
        import soundfile as sf
        sf.write(output_path, audio_opt, tgt_sr)
        print(f"Conversion successful! Saved to: {output_path}")
        return True
    else:
        print(f"Conversion failed: {info}")
        return False

if __name__ == "__main__":
    input_audio = "reels_audio_esposa_voice.wav" # User said this is the created audio
    model = "esposa_voice.pth"
    output_audio = "reels_audio_esposa_CONVERTED.wav"
    
    if os.path.exists(input_audio):
        run_conversion(input_audio, output_audio, model)
    else:
        print(f"Error: Input file {input_audio} not found in current directory.")
