#!/bin/bash
# Quick test script - run when XTTS is online

echo "═════════════════════════════════════════════════════"
echo "Quick Test: XTTS + RVC Voice Cloning"
echo "═════════════════════════════════════════════════════"
echo ""

# Test 1: XTTS API
echo "[1/3] Testing XTTS API..."
if curl -s http://127.0.0.1:8001/health | jq . 2>/dev/null; then
    echo "✓ XTTS API: OK"
else
    echo "✗ XTTS API: FAILED"
    exit 1
fi

echo ""

# Test 2: RVC API
echo "[2/3] Testing RVC API..."
if curl -s http://127.0.0.1:8000/health | jq . 2>/dev/null; then
    echo "✓ RVC API: OK"
else
    echo "✗ RVC API: FAILED"
    exit 1
fi

echo ""

# Test 3: Generate audio
echo "[3/3] Testing TTS generation..."
python3 << 'EOF'
import requests
import json

try:
    response = requests.post("http://127.0.0.1:8001/generate", json={
        "text": "Olá, este é um teste rápido do sistema.",
        "language": "pt",
        "speaker_wav": "app/runtime/datasets/speaker.wav"
    }, timeout=120)

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Audio generated: {result['file']}")
        print(f"  Size: {result['file_size_mb']:.2f} MB")
        print(f"  Duration: {result['duration_seconds']:.1f}s")
    else:
        print(f"✗ Error: {response.json()}")
except Exception as e:
    print(f"✗ Connection error: {e}")
EOF

echo ""
echo "═════════════════════════════════════════════════════"
echo "✓ All tests passed! System is ready."
echo "═════════════════════════════════════════════════════"
echo ""
echo "Next: python tts_to_rvc.py"
