#!/usr/bin/env python3
"""
Voice Cloning System Tester
Testa RVC Voice Conversion e XTTS Text-to-Speech
"""

import os
import sys
import json
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 60)
print("VOICE CLONING SYSTEM TEST")
print("=" * 60)
print()

# Test 1: Check Backend Status
print("[1/3] Checking backend API...")
try:
    import requests
    health = requests.get("http://127.0.0.1:8000/health", timeout=2).json()
    print(f"  Status: {health['status']}")
    print(f"  RVC: {health.get('rvc_env_available')}")
    print(f"  XTTS: {health.get('xtts_env_available')}")
    print(f"  Voices: {health.get('voices_count')}")
except Exception as e:
    print(f"  ERROR: {e}")
    print("  Make sure backend is running: start_all.bat or start_backend.bat")
    sys.exit(1)

print()

# Test 2: List Available Voices
print("[2/3] Available voices:")
try:
    voices_data = requests.get("http://127.0.0.1:8000/voices").json()
    for voice in voices_data.get("voices", []):
        print(f"  ✓ {voice['name']}: {voice['status']}")
        if voice['name'] == 'api_probe4':
            print(f"    (Wife's voice - ready to use!)")
except Exception as e:
    print(f"  ERROR: {e}")

print()

# Test 3: Test Frontend
print("[3/3] Frontend ready:")
print(f"  URL: http://localhost:3000")
print(f"  Status: Check in browser")

print()
print("=" * 60)
print("NEXT STEPS:")
print("=" * 60)
print()
print("Option 1: Use Web Interface")
print("  1. Open http://localhost:3000")
print("  2. Upload an audio file OR select 'api_probe4' to generate")
print("  3. Click 'Gerar Áudio' or 'Converter Voz'")
print()
print("Option 2: Use Python API (script)")
print("  python test_rvc_direct.py")
print()
print("Option 3: Use cURL")
print("  curl -X POST http://127.0.0.1:8000/convert_voice \\")
print("    -H 'Content-Type: application/json' \\")
print("    -d '{\"voice\":\"api_probe4\",\"input_path\":\"...\"}'")
print()
print("=" * 60)
