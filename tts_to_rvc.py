#!/usr/bin/env python3
"""
TTS (Docker) -> RVC (Windows)
Fluxo completo: Texto -> Áudio genérico -> Voz da esposa
"""

import requests
import time
import sys
from pathlib import Path

# APIs
XTTS_API = "http://127.0.0.1:8001"
RVC_API = "http://127.0.0.1:8000"

def generate_tts(text, language="pt"):
    """Gera áudio com XTTS no Docker"""
    print(f"\n{'=' * 60}")
    print(f"1️⃣  GERANDO ÁUDIO COM TTS (Docker)")
    print(f"{'=' * 60}")
    print(f"Texto: {text[:60]}...")
    print(f"Idioma: {language}")

    # Arquivo de referência (sua esposa)
    speaker_wav = str(Path("app/runtime/datasets/speaker.wav"))

    try:
        payload = {
            "text": text,
            "language": language,
            "speaker_wav": speaker_wav
        }

        response = requests.post(
            f"{XTTS_API}/generate",
            json=payload,
            timeout=300
        )

        if response.status_code == 200:
            result = response.json()
            audio_file = result["file"]
            duration = result.get("duration_seconds", 0)
            size = result.get("file_size_mb", 0)

            print(f"\n✓ TTS concluído!")
            print(f"  Arquivo: {audio_file}")
            print(f"  Duração: {duration:.1f}s")
            print(f"  Tamanho: {size:.2f} MB")
            return audio_file
        else:
            error = response.json()
            print(f"\n✗ Erro TTS ({response.status_code}): {error.get('detail', 'Desconhecido')}")
            return None

    except requests.exceptions.ConnectionError:
        print(f"\n✗ Erro: Não consegui conectar ao XTTS")
        print(f"   Execute: cd docker-xtts && docker-compose up")
        return None
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        return None

def convert_with_rvc(audio_file, voice="api_probe4"):
    """Converte áudio com RVC"""
    print(f"\n{'=' * 60}")
    print(f"2️⃣  CONVERTENDO COM RVC (sua esposa)")
    print(f"{'=' * 60}")
    print(f"Áudio: {audio_file}")
    print(f"Voz: {voice}")

    # Instruções para usar web interface
    print(f"\n📝 Use a web interface para converter:")
    print(f"   1. Abra http://localhost:3000")
    print(f"   2. Na aba 'Converter Voz':")
    print(f"      - Clique em 'Selecionar arquivo'")
    print(f"      - Escolha: {audio_file}")
    print(f"      - Voz alvo: {voice}")
    print(f"      - Clique: 'Converter Voz'")
    print(f"\n   OU use esta URL (copie):")
    print(f"   http://localhost:3000?file={audio_file}&voice={voice}")

    return audio_file

def main():
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "TTS (Docker) → RVC → Sua Esposa" + " " * 16 + "║")
    print("╚" + "═" * 58 + "╝")

    # Verificar backends
    print("\n🔍 Verificando serviços...")

    try:
        xtts_health = requests.get(f"{XTTS_API}/health", timeout=2).json()
        xtts_status = f"✓ XTTS: {xtts_health.get('status', 'unknown')}"
    except:
        xtts_status = "✗ XTTS: NÃO CONECTADO"

    try:
        rvc_health = requests.get(f"{RVC_API}/health", timeout=2).json()
        rvc_status = f"✓ RVC: {rvc_health.get('status', 'unknown')}"
    except:
        rvc_status = "✗ RVC: NÃO CONECTADO"

    print(f"  {xtts_status}")
    print(f"  {rvc_status}")

    # Verificar se tudo está rodando
    if "NÃO" in xtts_status or "NÃO" in rvc_status:
        print(f"\n⚠️  Serviços offline!")
        if "NÃO" in xtts_status:
            print(f"\n   Para iniciar XTTS:")
            print(f"   cd docker-xtts")
            print(f"   docker-compose up")
        if "NÃO" in rvc_status:
            print(f"\n   Para iniciar RVC:")
            print(f"   start_backend.bat")
        return

    print(f"\n✓ Todos os serviços online!")

    # Texto para testar
    text = "Olá, meu nome é Camila. Este é um teste do sistema de geração de áudio com minha voz clonada."

    print(f"\n{'=' * 60}")
    print(f"TESTE DE FLUXO COMPLETO")
    print(f"{'=' * 60}")

    # Gerar com TTS
    audio_file = generate_tts(text, language="pt")

    if audio_file and Path(audio_file).exists():
        # Converter com RVC
        final_audio = convert_with_rvc(audio_file)

        print(f"\n{'=' * 60}")
        print(f"✓ FLUXO PRONTO!")
        print(f"{'=' * 60}")
        print(f"\n📁 Arquivo TTS: {audio_file}")
        print(f"   Pronto para converter com RVC na web interface")
        print(f"\n🌐 Web: http://localhost:3000")

    else:
        print(f"\n{'=' * 60}")
        print(f"✗ FALHA NA GERAÇÃO TTS")
        print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
