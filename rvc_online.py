#!/usr/bin/env python3
"""
RVC Voice Conversion via Hugging Face Spaces API
Free online service - no local dependencies needed
"""

import requests
import sys
from pathlib import Path
import time

def convert_voice_online(audio_file, speaker_id=0, max_retries=3):
    """
    Convert voice using online RVC API via Hugging Face

    Uses the RVC Space: https://huggingface.co/spaces/akhaliq/RVC
    """

    print("="*70)
    print("RVC Voice Conversion - Online via Hugging Face")
    print("="*70)
    print()

    # Check if audio file exists
    if not Path(audio_file).exists():
        print(f"[ERROR] Audio file not found: {audio_file}")
        return False

    file_size = Path(audio_file).stat().st_size / (1024 * 1024)
    print(f"Input file: {audio_file}")
    print(f"File size: {file_size:.1f} MB")
    print(f"Speaker ID: {speaker_id}")
    print()

    # Hugging Face Spaces API endpoint
    # Using the RVC Space by akhaliq
    api_url = "https://akhaliq-rvc.hf.space/api/predict"

    print("Connecting to online RVC service...")
    print(f"API: {api_url}")
    print()

    try:
        # Read audio file
        print(f"Reading audio file...")
        with open(audio_file, 'rb') as f:
            audio_data = f.read()

        print(f"[OK] Audio loaded: {len(audio_data)} bytes")
        print()

        # Prepare request data
        # The RVC Space expects specific format
        print("Preparing request...")

        files = {
            'input_audio': (audio_file, audio_data, 'audio/mpeg'),
        }

        data = {
            'speaker_id': str(speaker_id),
            'f0_up_key': '0',
            'f0_method': 'dio',
        }

        print("[INFO] Sending audio to server for conversion...")
        print("This may take 2-5 minutes depending on server load...")
        print()

        # Send request with retry logic
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries}...")

                response = requests.post(
                    api_url,
                    files=files,
                    data=data,
                    timeout=300  # 5 minute timeout
                )

                if response.status_code == 200:
                    print(f"[OK] Server responded successfully")
                    break
                else:
                    print(f"[WARNING] Server returned status {response.status_code}")
                    if attempt < max_retries - 1:
                        print(f"Retrying in 5 seconds...")
                        time.sleep(5)
                    continue

            except requests.exceptions.Timeout:
                print(f"[WARNING] Request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    print(f"Retrying in 10 seconds...")
                    time.sleep(10)
                else:
                    print(f"[ERROR] Timeout after {max_retries} attempts")
                    return False

            except requests.exceptions.ConnectionError:
                print(f"[WARNING] Connection error (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    print(f"Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print(f"[ERROR] Connection failed after {max_retries} attempts")
                    return False

        # Check if request was successful
        if response.status_code != 200:
            print(f"[ERROR] Server error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False

        # Save output
        output_file = "reels_audio_esposa_voice.wav"

        print()
        print("Saving output...")

        # The response might be the audio file or a JSON with file path
        if 'application/json' in response.headers.get('content-type', ''):
            # JSON response - might contain file URL
            import json
            result = response.json()
            print(f"[INFO] Server response: {result}")

            # Download the file if URL provided
            if 'output_audio' in result:
                audio_url = result['output_audio']
                print(f"[INFO] Downloading audio from: {audio_url}")

                audio_response = requests.get(audio_url)
                with open(output_file, 'wb') as f:
                    f.write(audio_response.content)
            else:
                print(f"[WARNING] Unexpected response format")
                return False
        else:
            # Direct audio file
            with open(output_file, 'wb') as f:
                f.write(response.content)

        # Verify output
        if Path(output_file).exists():
            output_size = Path(output_file).stat().st_size / (1024 * 1024)

            print(f"[OK] Output saved: {output_file}")
            print(f"     Size: {output_size:.1f} MB")
            print()
            print("="*70)
            print("[SUCCESS] Voice Conversion Complete!")
            print("="*70)
            print()
            print(f"Your audio with wife's voice is ready:")
            print(f"  {Path(output_file).absolute()}")
            print()
            print("You can now:")
            print("  1. Download the file")
            print("  2. Add to your video editor")
            print("  3. Post to Instagram/TikTok Reels")
            print()

            return True
        else:
            print(f"[ERROR] Output file was not created")
            return False

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # Files
    input_audio = "tts_temp.mp3"
    speaker_id = 0

    # Check if file exists
    if not Path(input_audio).exists():
        print(f"[ERROR] Input file not found: {input_audio}")
        print()
        print("Make sure you have:")
        print(f"  - {input_audio} (your TTS audio)")
        return False

    # Run conversion
    success = convert_voice_online(input_audio, speaker_id)

    if not success:
        print()
        print("[INFO] Online API may be unavailable")
        print()
        print("Alternative options:")
        print("1. Try again in a few moments (server might be busy)")
        print("2. Use Google Colab PRO ($10)")
        print("3. Wait and retry later")

    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
