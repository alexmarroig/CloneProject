import os
import sys
import torch
from pathlib import Path

now_dir = os.getcwd()
sys.path.append(now_dir)

from configs.config import Config
from infer.modules.vc.modules import VC
from infer.modules.vc.utils import load_hubert
from infer.modules.vc.pipeline import Pipeline
import librosa
import numpy as np

def debug_pipeline():
    os.environ["weight_root"] = os.path.join(now_dir, "assets", "weights")
    os.environ["index_root"] = os.path.join(now_dir, "logs")
    os.environ["rmvpe_root"] = os.path.join(now_dir, "assets", "rmvpe")
    
    config = Config()
    config.device = "cpu"
    config.is_half = False
    
    vc = VC(config)
    vc.get_vc("esposa_voice.pth")
    vc.hubert_model = load_hubert(config)
    
    # Load 1 second of audio
    audio, sr = librosa.load("reels_audio_esposa_voice_10s.wav", sr=16000)
    audio = audio[:16000] # 1 second
    audio_t = torch.FloatTensor(audio)
    print(f"Input audio: min={audio_t.min():.4f}, max={audio_t.max():.4f}, has_nan={torch.isnan(audio_t).any().item()}")
    
    pipeline = vc.pipeline
    
    device = pipeline.device
    is_half = pipeline.is_half
    
    audio_t = audio_t.to(device)
    if is_half: audio_t = audio_t.half()
        
    with torch.no_grad():
        # Hubert
        feats = vc.hubert_model(audio_t.unsqueeze(0))["last_hidden_state"]
        print(f"Hubert feats: shape={feats.shape}, min={feats.min():.4f}, max={feats.max():.4f}, mean={feats.mean():.4f}, has_nan={torch.isnan(feats).any().item()}")
        
        # F0 extraction
        pitch, pitchf = pipeline.get_f0(0.0, None, audio, 16000, 160, "pm", None, 0)
        print(f"Pitch: shape={pitch.shape}, min={pitch.min():.4f}, max={pitch.max():.4f}, has_nan={np.isnan(pitch).any()}")
        
        # Generator
        # Create minimal tensors for generator input
        # Note: requires properly padded feats, etc. We will just use the pipeline class directly 
        p_len = audio.shape[0] // 160
        feats = pipeline.get_f0_feats(feats, pitch, pitchf, p_len)
        print(f"Proc feats: min={feats.min():.4f}, max={feats.max():.4f}, has_nan={torch.isnan(feats).any().item()}")
        
        speaker_id = torch.LongTensor([0]).to(device)
        feats = feats.to(device)
        if pipeline.is_half: feats = feats.half()
            
        print("Running generator...")
        audio_opt = vc.net_g.infer(feats, p_len=torch.LongTensor([p_len]).to(device), sid=speaker_id)[0][0, 0]
        print(f"Generator output: min={audio_opt.min():.4f}, max={audio_opt.max():.4f}, mean={audio_opt.mean():.4f}, has_nan={torch.isnan(audio_opt).any().item()}")
        
if __name__ == "__main__":
    debug_pipeline()
