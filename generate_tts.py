import asyncio
import os
import edge_tts

async def amain(text: str, voice: str, output_file: str) -> None:
    """Generate TTS audio using edge-tts."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

if __name__ == "__main__":
    # Test text in Portuguese
    TEXT = "Olá! Este é um teste da nossa nova pipeline de automação para vídeos. O objetivo é criar conteúdos de alta qualidade com a minha própria voz clonada, de forma rápida e eficiente. O que você achou do resultado?"
    VOICE = "pt-BR-AntonioNeural"  # High quality male voice
    OUTPUT_DIR = "assets/tts_outputs"
    OUTPUT_FILE = os.path.join(OUTPUT_DIR, "base_audio.wav")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"Generating TTS for: '{TEXT}'")
    print(f"Using voice: {VOICE}")
    
    asyncio.run(amain(TEXT, VOICE, OUTPUT_FILE))
    
    if os.path.exists(OUTPUT_FILE):
        print(f"Success! Audio saved to: {OUTPUT_FILE}")
        print(f"File size: {os.path.getsize(OUTPUT_FILE)} bytes")
    else:
        print("Error: Audio file was not created.")
