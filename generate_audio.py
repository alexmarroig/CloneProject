#!/usr/bin/env python3
"""
Voice Cloning Audio Generator
Gera áudio com a voz clonada da sua esposa usando XTTS ou RVC
"""

import requests
import json
import time
import sys
from pathlib import Path

API_URL = "http://127.0.0.1:8000"

def generate_with_xtts(text: str, language: str = "pt", voice: str = "api_probe4"):
    """Generate audio using XTTS (text-to-speech with voice cloning)"""
    print(f"\nGerando áudio com XTTS...")
    print(f"Texto: {text[:50]}...")
    print(f"Voz: {voice}")
    print(f"Idioma: {language}")
    print()

    payload = {
        "text": text,
        "voice": voice,
        "language": language,
        "speed": 1.0,
        "temperature": 0.7
    }

    # Submit job
    response = requests.post(f"{API_URL}/generate_voice", json=payload)
    if response.status_code != 200:
        print(f"Erro ao enviar: {response.status_code}")
        print(response.text)
        return None

    job_data = response.json()
    job_id = job_data["job_id"]

    # Poll for completion
    print(f"Job ID: {job_id}")
    print("Aguardando conclusão...")

    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed > 300:  # 5 minutes timeout
            print("Timeout!")
            return None

        status_response = requests.get(f"{API_URL}/jobs/{job_id}")
        job_status = status_response.json()
        status = job_status["status"]
        progress = job_status.get("progress", 0)

        print(f"\r[{int(elapsed):3d}s] {status:10s} ({progress}%)", end="", flush=True)

        if status in ["completed", "failed"]:
            print()  # New line
            break

        time.sleep(2)

    if job_status["status"] == "completed":
        artifacts = job_status.get("artifacts", [])
        if artifacts and Path(artifacts[0]).exists():
            file_size = Path(artifacts[0]).stat().st_size / (1024 * 1024)
            print(f"\n✓ Sucesso!")
            print(f"Arquivo: {artifacts[0]}")
            print(f"Tamanho: {file_size:.2f} MB")
            return artifacts[0]
        else:
            print("\nErro: Arquivo não encontrado")
            return None
    else:
        error = job_status.get("error", "Erro desconhecido")
        print(f"\nErro: {error[:200]}")
        return None

def main():
    print("=" * 60)
    print("GERADOR DE ÁUDIO COM VOZ CLONADA")
    print("=" * 60)

    # Check API is running
    try:
        health = requests.get(f"{API_URL}/health", timeout=2).json()
        print(f"\nBackend: {health['status']}")
    except:
        print("\nErro: Backend não está rodando!")
        print("Execute: start_all.bat")
        return

    # Get available voices
    try:
        voices_data = requests.get(f"{API_URL}/voices").json()
        voices = [v['name'] for v in voices_data.get("voices", [])]
        print(f"Vozes disponíveis: {', '.join(voices)}")
    except:
        print("Erro ao listar vozes")
        voices = ["api_probe4"]

    # Example: Generate audio
    text = "Olá, meu nome é Camila. Este é um teste do sistema de geração de áudio com voz clonada."

    print("\n" + "=" * 60)
    print("TESTE DE GERAÇÃO")
    print("=" * 60)

    output_file = generate_with_xtts(text, language="pt", voice="api_probe4")

    if output_file:
        print(f"\n✓ Áudio gerado com sucesso!")
        print(f"Localização: {output_file}")
        print("\nPróximos passos:")
        print("1. Ouvir o áudio gerado")
        print("2. Usar em HeyGen para criar vídeos")
        print("3. Automatizar o processo")
    else:
        print("\n✗ Falha na geração")

if __name__ == "__main__":
    main()
