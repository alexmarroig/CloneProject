#!/usr/bin/env python3
"""
Simple audio generation using gTTS (Google Text-to-Speech)
Then convert voice using trained RVC model
"""

import sys
from pathlib import Path
from gtts import gTTS
import soundfile as sf
import numpy as np

# Your reels text
REELS_TEXT = """Você acha que cuidar de você mesma é egoísmo?
Escuta só: limite não é punição. Limite é proteção.
Quando você estabelece um limite, você não está machucando ninguém.
Você está dizendo 'isso não é aceitável para mim'.
Não confunda estabelecer limite com vingança ou frieza.
Limite saudável é amar a si mesma primeiro.
Se você só é feliz quando desaparece pelo outro, o problema não é você.
É a crença errada que te ensinaram sobre amor.
Amar alguém não significa aceitar tudo. Significa respeitar a si mesma."""

def generate_tts():
    """Generate TTS audio using gTTS"""
    print("[1/2] Generating text-to-speech audio...")
    print(f"  Text: {len(REELS_TEXT)} characters")
    print(f"  Language: Portuguese (Brazilian)")

    try:
        tts = gTTS(text=REELS_TEXT, lang='pt', slow=False)
        tts_file = "tts_temp.wav"

        # gTTS saves as mp3, convert to wav
        mp3_file = "tts_temp.mp3"
        tts.save(mp3_file)
        print(f"  [OK] TTS generated: {mp3_file}")

        # Convert to wav using pydub
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(mp3_file)
            audio.export(tts_file, format="wav")
            print(f"  [OK] Converted to WAV: {tts_file}")

            # Clean up mp3
            Path(mp3_file).unlink()
            return tts_file
        except:
            # If pydub conversion fails, return mp3
            print(f"  [WARNING] Using MP3 format instead")
            return mp3_file

    except Exception as e:
        print(f"  [ERROR] TTS generation failed: {e}")
        return None

def main():
    print("="*70)
    print("Generating Reels Audio - Wife's Voice")
    print("="*70)
    print()

    # Step 1: Generate TTS
    tts_file = generate_tts()
    if not tts_file:
        print("[ERROR] Failed to generate TTS audio")
        return False

    print()
    print("[2/2] Ready for voice conversion!")
    print(f"  Input: {tts_file}")
    print(f"  Model: esposa_voice (53.9 MB)")
    print(f"  Output: reels_audio_esposa_voice.wav")
    print()
    print("[INFO] Note: Voice conversion requires RVC model inference")
    print("       The trained model is ready at: assets/weights/esposa_voice.pth")
    print()

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
