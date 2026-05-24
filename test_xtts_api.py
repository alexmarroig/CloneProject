#!/usr/bin/env python3
"""
Testa XTTS API rapidamente
"""

import requests
import time
from pathlib import Path

XTTS_API = "http://127.0.0.1:8001"

def wait_for_xtts(timeout=600):
    """Aguarda XTTS ficar online"""
    print("⏳ Aguardando XTTS ficar online...")
    start = time.time()

    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{XTTS_API}/health", timeout=2)
            if resp.status_code == 200:
                health = resp.json()
                print(f"\n✓ XTTS Online!")
                print(f"  Status: {health.get('status')}")
                print(f"  Modelo: {health.get('model')}")
                print(f"  Carregado: {health.get('model_loaded')}")
                return True
        except:
            pass

        elapsed = time.time() - start
        print(f"\r  [{int(elapsed):3d}s] Tentando conectar...", end="", flush=True)
        time.sleep(5)

    print(f"\n✗ Timeout! XTTS não respondeu em {timeout}s")
    return False

def test_generate():
    """Testa geração de áudio"""
    print("\n" + "=" * 60)
    print("TESTANDO GERAÇÃO TTS")
    print("=" * 60)

    speaker_wav = str(Path("app/runtime/datasets/speaker.wav"))

    if not Path(speaker_wav).exists():
        print(f"✗ Arquivo não encontrado: {speaker_wav}")
        return False

    payload = {
        "text": "Olá, teste de síntese de voz com inteligência artificial.",
        "language": "pt",
        "speaker_wav": speaker_wav
    }

    try:
        print(f"\n📝 Gerando áudio...")
        print(f"   Texto: {payload['text']}")
        print(f"   Referência: {speaker_wav}")

        response = requests.post(
            f"{XTTS_API}/generate",
            json=payload,
            timeout=300
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Sucesso!")
            print(f"  Arquivo: {result['file']}")
            print(f"  ID: {result['output_id']}")
            print(f"  Duração: {result['duration_seconds']:.1f}s")
            print(f"  Tamanho: {result['file_size_mb']:.2f} MB")
            return True
        else:
            error = response.json()
            print(f"✗ Erro: {error.get('detail', 'Desconhecido')}")
            return False

    except Exception as e:
        print(f"✗ Erro: {e}")
        return False

def main():
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "TESTE XTTS API" + " " * 31 + "║")
    print("╚" + "═" * 58 + "╝")

    # Aguardar XTTS
    if not wait_for_xtts(timeout=600):
        print("\n⚠️  XTTS não iniciou!")
        return

    # Testar geração
    if test_generate():
        print("\n" + "=" * 60)
        print("✓ TODOS OS TESTES PASSARAM!")
        print("=" * 60)
        print("\nAgora pode rodar: python tts_to_rvc.py")
    else:
        print("\n✗ Teste falhou!")

if __name__ == "__main__":
    main()
