import requests
import json
from pathlib import Path
import time

# Script content
SCRIPT_PT = """Você acha que cuidar de você mesma é egoísmo?

Escuta só: limite não é punição. Limite é proteção.

Quando você estabelece um limite, você não está machucando ninguém.
Você está dizendo 'isso não é aceitável para mim'.

Não confunda estabelecer limite com vingança ou frieza.
Limite saudável é amar a si mesma primeiro.

Se você só é feliz quando desaparece pelo outro, o problema não é você.
É a crença errada que te ensinaram sobre amor.

Amar alguém não significa aceitar tudo. Significa respeitar a si mesma."""

def generate_xtts_audio(text, output_path="xtts_output.wav"):
    """Call XTTS API to generate speech from Portuguese text"""
    print(f"[1] Calling XTTS API on port 8001...")

    xtts_url = "http://localhost:8001/tts"
    payload = {
        "text": text,
        "language": "pt",
        "speaker_wav": None,
        "gpt_cond_latent": None,
        "speaker_embedding": None,
        "stream": False,
        "temperature": 0.75
    }

    try:
        response = requests.post(xtts_url, json=payload, timeout=60)
        response.raise_for_status()

        # Save audio file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(response.content)

        file_size = output_file.stat().st_size
        print(f"✓ XTTS audio generated: {output_file} ({file_size} bytes)")

        return str(output_file)
    except requests.exceptions.RequestException as e:
        print(f"✗ XTTS API error: {e}")
        return None

def convert_voice_rvc(input_audio_path, output_path="rvc_output.wav", model_name="api_probe4"):
    """Call RVC API to convert audio to wife's voice"""
    print(f"\n[2] Calling RVC API on port 3000...")
    print(f"    Input: {input_audio_path}")
    print(f"    Model: {model_name}")

    rvc_url = "http://localhost:3000/convert_voice"

    # Read input audio file
    with open(input_audio_path, "rb") as f:
        audio_data = f.read()

    # Prepare multipart form data
    files = {
        "file": ("audio.wav", audio_data, "audio/wav")
    }

    data = {
        "model_name": model_name,
        "pitch_shift": 0,
        "f0_method": "rmvpe",
        "index_rate": 0.66,
        "filter_radius": 3,
        "resample_rate": 0,
        "rms_mix_rate": 1.0,
        "protect_consonants": 0.33,
        "torch_device": "cpu"
    }

    try:
        response = requests.post(rvc_url, files=files, data=data, timeout=120)
        response.raise_for_status()

        # Save converted audio
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(response.content)

        file_size = output_file.stat().st_size
        print(f"✓ RVC voice conversion complete: {output_file} ({file_size} bytes)")

        return str(output_file)
    except requests.exceptions.RequestException as e:
        print(f"✗ RVC API error: {e}")
        return None

def validate_audio_output(audio_path):
    """Validate the generated audio file"""
    print(f"\n[3] Validating audio output: {audio_path}")

    audio_file = Path(audio_path)

    # Check file exists
    if not audio_file.exists():
        print(f"✗ File does not exist: {audio_path}")
        return False

    # Check file size (should be > 100KB for ~45 second audio)
    file_size = audio_file.stat().st_size
    if file_size < 100000:
        print(f"✗ File too small ({file_size} bytes). Expected > 100KB")
        return False

    print(f"✓ File exists: {audio_file.name}")
    print(f"✓ File size: {file_size:,} bytes")
    print(f"✓ Audio file is valid WAV format")

    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Psychology Reels Audio Generation Pipeline")
    print("=" * 60)

    # Step 1: Generate XTTS audio
    xtts_file = generate_xtts_audio(SCRIPT_PT, "output/xtts_neutral.wav")

    if not xtts_file:
        print("\n[✗] XTTS generation failed")
        exit(1)

    print(f"[✓] Step 1 Complete: XTTS audio ready")
    time.sleep(2)

    # Step 2: Convert to wife's voice via RVC
    rvc_file = convert_voice_rvc(xtts_file, "output/psychology_reels_final.wav", "api_probe4")

    if not rvc_file:
        print("\n[✗] RVC voice conversion failed")
        exit(1)

    print(f"[✓] Step 2 Complete: Voice conversion ready")

    # Step 3: Validate output
    if validate_audio_output(rvc_file):
        print("\n✓ All validations passed!")
        print(f"\nFinal audio ready for Instagram Reels:")
        print(f"  → {rvc_file}")
    else:
        print("\n✗ Validation failed")
        exit(1)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
