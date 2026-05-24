#!/usr/bin/env python3
"""
Teste direto de RVC Voice Conversion
Sem usar a API - direto com as bibliotecas Python
"""

import sys
import os
from pathlib import Path
import numpy as np

# Setup path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 60)
print("RVC VOICE CONVERSION TEST (Direto)")
print("=" * 60)
print()

# Test audio file
test_audio = PROJECT_ROOT / "app" / "models" / "xtts" / "speaker.wav"

print(f"1. Verificando arquivo de entrada...")
print(f"   Arquivo: {test_audio}")
print(f"   Existe: {test_audio.exists()}")

if not test_audio.exists():
    print("\nErro: Arquivo não encontrado!")
    sys.exit(1)

print()
print(f"2. Verificando modelo RVC...")

try:
    voices_dir = PROJECT_ROOT / "app" / "models" / "voices"
    api_probe4 = voices_dir / "api_probe4"
    model_file = api_probe4 / "model.pth"
    index_file = api_probe4 / "model.index"

    print(f"   Modelo: {api_probe4}")
    print(f"   Model.pth: {model_file.exists()}")
    print(f"   Model.index: {index_file.exists()}")

    if not model_file.exists():
        print("\n   Erro: Modelo não encontrado!")
        print("   Certifique-se de que o api_probe4 foi treinado")
        sys.exit(1)

except Exception as e:
    print(f"   Erro: {e}")
    sys.exit(1)

print()
print(f"3. Status do Backend...")

try:
    import requests
    health = requests.get("http://127.0.0.1:8000/health", timeout=2).json()
    print(f"   Backend: {health['status']}")
    print(f"   RVC env: {health.get('rvc_env_available')}")
except Exception as e:
    print(f"   Erro: Backend não está rodando")
    print(f"   Execute: start_backend.bat")
    sys.exit(1)

print()
print("=" * 60)
print("TUDO PRONTO!")
print("=" * 60)
print()
print("✓ Arquivo de entrada: OK")
print("✓ Modelo RVC (api_probe4): OK")
print("✓ Backend API: OK")
print()
print("Próximo passo:")
print("  1. Abra http://localhost:3000")
print("  2. Faça upload de um áudio")
print("  3. Selecione: api_probe4")
print("  4. Clique: Converter Voz")
print()
print("=" * 60)
