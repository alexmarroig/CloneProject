import asyncio
import os
import subprocess
from edge_tts import Communicate

async def generate_tts(text, output_file):
    voice = "pt-BR-AntonioNeural" # Good Brazilian male voice
    communicate = Communicate(text, voice)
    await communicate.save(output_file)
    print(f"TTS generated: {output_file}")

def convert_to_wav(input_file, output_file):
    # Using ffmpeg directly
    cmd = f"ffmpeg -i {input_file} -y {output_file}"
    subprocess.run(cmd, shell=True, check=True)
    print(f"Converted to WAV: {output_file}")

def run_rvc_inference(input_wav, output_wav, model_name):
    python_exe = os.path.join("venv_rvc", "Scripts", "python.exe")
    infer_cli = os.path.join("tools", "infer_cli.py")
    
    # Parameters for RVC
    # f0method: 'rmvpe' is usually best, but let's check what's available.
    # defaults to 'harvest' if not specified.
    cmd = [
        python_exe, infer_cli,
        "--input_path", input_wav,
        "--opt_path", output_wav,
        "--model_name", model_name,
        "--f0method", "rmvpe", # Trying RMVPE first
        "--device", "cpu",     # Force CPU as CUDA was not detected
        "--is_half", "False",  # CPU needs float32
        "--f0up_key", "0"      # No pitch shift
    ]
    
    print(f"Running RVC inference: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("RVC Error:")
        print(result.stdout)
        print(result.stderr)
        # Fallback to 'harvest' if 'rmvpe' fails due to missing weights
        print("Retrying with harvest...")
        cmd[cmd.index("rmvpe")] = "harvest"
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("RVC Error (Harvest):")
            print(result.stdout)
            print(result.stderr)
            return False
    
    print(f"Voice cloning complete: {output_wav}")
    return True

async def main():
    text = "Olá! Este é um teste do meu clone de voz usando o modelo R V C. Espero que a qualidade esteja boa!"
    temp_mp3 = "temp_test.mp3"
    temp_wav = "temp_test.wav"
    final_wav = "alex_voice_clone_test.wav"
    model_name = "alex_voice.pth" # Looking in assets/weights
    
    # 1. Generate TTS
    await generate_tts(text, temp_mp3)
    
    # 2. Convert to WAV
    try:
        convert_to_wav(temp_mp3, temp_wav)
    except Exception as e:
        print(f"FFmpeg failed: {e}")
        return

    # 3. Run RVC
    success = run_rvc_inference(temp_wav, final_wav, model_name)
    
    if success:
        print("\nSUCESSO!")
        print(f"O arquivo final está em: {os.path.abspath(final_wav)}")
    else:
        print("\nFalha na conversão final.")

if __name__ == "__main__":
    asyncio.run(main())
