# 🐳 XTTS + RVC Voice Cloning - Guia Docker

## O que é?

Sistema de clonagem de voz em 2 passos:
1. **XTTS** (em Docker) → Gera áudio de texto (TTS)
2. **RVC** (Windows) → Converte para voz da sua esposa

## Arquitetura

```
Texto
  ↓
[XTTS - Docker] → Áudio genérico (Camila falando)
  ↓
[RVC - Windows] → Áudio convertido (sua esposa falando)
  ↓
Resultado final
```

## Iniciar o Sistema

### Terminal 1: RVC Backend
```bash
start_backend.bat
```
Espere até ver: `Uvicorn running on http://127.0.0.1:8000`

### Terminal 2: XTTS Docker
```bash
cd docker-xtts
docker-compose up
```
Espere até ver: `Uvicorn running on http://0.0.0.0:8001`
(Primeira vez leva ~15 minutos)

### Terminal 3: Frontend (opcional)
```bash
start_frontend.bat
```
Acesse: http://localhost:3000

## Usar o Sistema

### Opção A: Script Python (Automático)
```bash
python tts_to_rvc.py
```

Fluxo:
1. Gera áudio com XTTS
2. Mostra instruções para converter com RVC
3. Abre web interface

### Opção B: Web Interface Manual
1. Abra http://localhost:3000
2. Aba "Converter Voz":
   - Selecione arquivo: `app/runtime/datasets/tts_*.wav`
   - Voz: `api_probe4`
   - Clique: "Converter Voz"

### Opção C: API Direta
```python
import requests

# Gerar TTS
response = requests.post("http://127.0.0.1:8001/generate", json={
    "text": "Seu texto aqui",
    "language": "pt",
    "speaker_wav": "app/runtime/datasets/speaker.wav"
})

audio_file = response.json()["file"]
print(f"Áudio gerado: {audio_file}")
```

## Testes

### Teste Rápido
```bash
python test_xtts_api.py
```

### Teste Completo
```bash
python tts_to_rvc.py
```

## Arquivos e Pastas

```
docker-xtts/
├── Dockerfile           # Imagem Linux com XTTS
├── docker-compose.yml   # Configuração do container
├── xtts_server.py      # API FastAPI do XTTS
└── requirements-xtts.txt # Dependências

app/runtime/datasets/   # Onde ficam os áudios gerados
├── speaker.wav         # Referência (sua esposa)
└── tts_*.wav           # Áudios gerados pelo XTTS
```

## Portas Padrão

- **XTTS API**: http://127.0.0.1:8001
- **RVC API**: http://127.0.0.1:8000
- **Frontend**: http://localhost:3000

## Troubleshooting

### XTTS não inicia
```bash
# Verificar logs
docker logs xtts-server

# Reconstruir
cd docker-xtts
docker-compose down
docker-compose up --build
```

### Docker não funciona
```bash
# Verificar se está rodando
docker ps

# Se não aparecer nada, inicie Docker Desktop
# Windows: Procure "Docker Desktop" no menu iniciar
```

### RVC não funciona
```bash
# Reiniciar backend
start_backend.bat
```

### Erro: "Arquivo não encontrado"
- Certifique-se que `app/runtime/datasets/speaker.wav` existe
- Se não existir, copie de `app/models/xtts/speaker.wav`

## Performance

| Componente | Tempo | Hardware |
|---|---|---|
| XTTS (TTS) | ~10-20s | CPU (Docker) |
| RVC (Conversão) | ~5-10s | CPU (Windows) |
| **Total** | **~15-30s** | - |

## Próximos Passos

1. ✓ XTTS gerou áudio
2. ✓ RVC converteu para sua esposa
3. → Usar em HeyGen para criar vídeos
4. → Automatizar o processo

## Integração HeyGen

Depois de gerar áudio com a voz da sua esposa:
1. Abra https://www.heygen.com
2. Faça upload do áudio gerado
3. Selecione avatar/apresentador
4. Gere vídeo com sua voz clonada!

## Suporte

- **Modelo RVC**: api_probe4 (sua esposa)
- **Modelo TTS**: XTTS v2 (Coqui)
- **Idiomas suportados**: Português, Inglês, Espanhol, etc.

---

Criado: 2026-03-17
Versão: 1.0
