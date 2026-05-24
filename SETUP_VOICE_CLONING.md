# 🎤 Guia Completo: Clonar a Voz da Sua Esposa

## Objetivo Final
Criar um workflow automatizado:
```
Voz da esposa → Treinar RVC → Gerar áudio clonado → HeyGen Avatar → Edição Automática → Vídeo Final
```

---

## ✅ PASSO 1: Verificar Setup (JÁ FEITO!)

### Status Atual:
- ✅ Backend FastAPI funcionando
- ✅ Frontend Next.js compilado
- ✅ Banco de dados SQLite criado
- ✅ RVC environment disponível
- ⚠️ XTTS environment (precisa verificar)

### Testar API:
```bash
# Terminal 1: Iniciar Backend
cd C:\Users\gaming\Desktop\Projetos\AI\Retrieval-based-Voice-Conversion-WebUI
python -m uvicorn app.backend.api.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Verificar health
curl http://127.0.0.1:8000/health
```

Esperado:
```json
{
  "status": "ok",
  "device": "auto",
  "ffmpeg_available": true,
  "xtts_env_available": true,
  "rvc_env_available": true,
  "voices_count": 0
}
```

---

## 📝 PASSO 2: Preparar Áudio da Esposa

### Requisitos de Qualidade:
- **Duração total:** 10-20 minutos (mínimo 10 minutos)
- **Formato:** WAV, MP3, FLAC (recomendado WAV)
- **Qualidade:** 44.1kHz ou superior, mono ou estéreo
- **Ruído de fundo:** Mínimo (silencioso é melhor)
- **Claro:** Voz clara, sem sussurros

### Onde Conseguir:
1. **Gravar você mesmo:**
   - Use seu smartphone
   - Estúdio caseiro silencioso
   - Leia um texto ou fale naturalmente

2. **Extrair de vídeos:**
   ```bash
   ffmpeg -i video.mp4 -q:a 9 -n audio.wav
   ```

### Preparar Arquivo:
- Salve como: `C:\Users\gaming\Desktop\Projetos\AI\Retrieval-based-Voice-Conversion-WebUI\app\runtime\datasets\spouse_voice\audio.wav`
- Crie a pasta `datasets\spouse_voice` se não existir

---

## 🚀 PASSO 3: Treinar o Modelo RVC

### Via Interface Web:

1. **Iniciar Frontend:**
   ```bash
   # Terminal 3
   cd C:\Users\gaming\Desktop\Projetos\AI\Retrieval-based-Voice-Conversion-WebUI\app\frontend
   npm run dev
   ```
   Acesse: `http://localhost:3000`

2. **Navegar para "Train":**
   - Voice Name: `spouse_voice`
   - Dataset Name: `spouse_voice`
   - Minutos de áudio: 10-20 minutos

3. **Configurações Recomendadas:**
   - Sample Rate: `40k` (melhor qualidade)
   - F0 Method: `rmvpe` (mais preciso)
   - Epochs: `300` (padrão)
   - Batch Size: `1` (se tiver VRAM limitada)
   - Learning Rate: `0.0001` (padrão)
   - Save Every Epoch: `10`
   - GPU Device: `auto` (deixar automático)

4. **Clicar em "Submit Training"**

### Via API (Alternativa):

```bash
curl -X POST http://127.0.0.1:8000/train_voice \
  -H "Content-Type: application/json" \
  -d '{
    "voice_name": "spouse_voice",
    "dataset_name": "spouse_voice",
    "dataset_path": ".",
    "silence_slicing": true,
    "normalize": true,
    "sample_rate": "40k",
    "f0_method": "rmvpe",
    "epochs": 300,
    "batch_size": 1,
    "learning_rate": 0.0001,
    "save_every_epoch": 10,
    "gpu_device": "auto",
    "use_gpu": true
  }'
```

### Tempo Estimado:
- 10 min de áudio: 2-4 horas em GPU
- 20 min de áudio: 4-8 horas em GPU

---

## 🎵 PASSO 4: Gerar Áudio Clonado

### Via Interface Web:

1. **Navegar para "Generate"**
2. **Configurações:**
   - Voice: `spouse_voice` (selecionará automaticamente)
   - Text: Cole seu roteiro/prompt
   - Language: `pt` (português)
   - Model: `tts_models/multilingual/multi-dataset/xtts_v2`
   - Speed: `1.0` (normal)
   - Temperature: `0.75` (natural)

3. **Clicar em "Submit Generate"**

### Via API:

```bash
curl -X POST http://127.0.0.1:8000/generate_voice \
  -H "Content-Type: application/json" \
  -d '{
    "voice": "spouse_voice",
    "text": "Seu roteiro aqui",
    "language": "pt",
    "model": "tts_models/multilingual/multi-dataset/xtts_v2",
    "speed": 1.0,
    "temperature": 0.75,
    "use_gpu": true
  }'
```

### Resultado:
- Áudio gerado em: `app/runtime/audio/output/`
- Formato: WAV (48kHz)
- Pronto para usar no HeyGen

---

## 🎬 PASSO 5: Integrar com HeyGen

### Como Usar no HeyGen:

1. **Criar Avatar no HeyGen:**
   - Vá para: https://www.heygen.com
   - Criar novo projeto
   - Upload do vídeo pessoal da esposa (opcional)

2. **Importar Áudio Gerado:**
   - No painel HeyGen, selecione "Upload Audio"
   - Selecione o arquivo WAV gerado em `app/runtime/audio/output/`
   - Configure o avatar para sincronizar com áudio

3. **Sincronizar Labial (Lip-sync):**
   - HeyGen fazará auto-sincronização
   - Tempo: ~2-5 minutos

4. **Exportar Vídeo:**
   - Clicar "Generate Video"
   - Selecionar resolução e formato
   - Baixar MP4 final

---

## ⚙️ PASSO 6: Automação (Opcional)

### Para Integrar com Software de Edição Automática:

1. **Salve script Python:**

```python
import os
import subprocess
from datetime import datetime

# Configurações
VOICE_ENGINE_API = "http://127.0.0.1:8000"
VOICE_NAME = "spouse_voice"
OUTPUT_DIR = "app/runtime/audio/output"

def generate_video_from_prompt(prompt_text):
    """Gera vídeo automático a partir de um roteiro"""

    # 1. Gerar áudio
    print(f"Gerando áudio para: {prompt_text[:50]}...")
    response = requests.post(
        f"{VOICE_ENGINE_API}/generate_voice",
        json={
            "voice": VOICE_NAME,
            "text": prompt_text,
            "language": "pt",
            "speed": 1.0
        }
    )
    job_id = response.json()["job_id"]

    # 2. Aguardar conclusão
    while True:
        status = requests.get(f"{VOICE_ENGINE_API}/jobs/{job_id}").json()
        if status["status"] == "completed":
            audio_file = status["artifacts"][0]["path"]
            break
        elif status["status"] == "failed":
            raise Exception(f"Falha na geração: {status['error']}")
        time.sleep(5)

    # 3. Enviar para HeyGen (requer API key)
    # ... implementar integração HeyGen

    # 4. Retornar URL do vídeo
    return video_url

if __name__ == "__main__":
    prompt = "Olá, meu nome é [Nome] e estou aqui para..."
    video_url = generate_video_from_prompt(prompt)
    print(f"Vídeo criado: {video_url}")
```

2. **Executar:**
```bash
python generate_video.py
```

---

## 📊 Monitoramento de Jobs

### Ver Status em Tempo Real:

**Web UI:** http://localhost:3000 → Aba "Jobs"

**Via API:**
```bash
# Listar todos os jobs
curl http://127.0.0.1:8000/jobs

# Ver job específico
curl http://127.0.0.1:8000/jobs/{job_id}

# Stream de eventos (tempo real)
curl http://127.0.0.1:8000/jobs/{job_id}/stream
```

---

## 🔧 Troubleshooting

### "XTTS Environment Not Available"
```bash
# Verificar Python do XTTS
ls app/runtime/envs/xtts/Scripts/python.exe

# Instalar dependências
app/runtime/envs/xtts/Scripts/python.exe -m pip install coqui-tts torch torchaudio
```

### "FFmpeg Not Found"
```bash
# Baixar ffmpeg
choco install ffmpeg  # Windows com Chocolatey
# ou
brew install ffmpeg   # macOS
```

### Áudio com Ruído/Qualidade Ruim
- Aumentar `silence_trimming` na preparação
- Usar áudio de melhor qualidade
- Aumentar minutos de treinamento (20+ min)

### Modelo Não Converge
- Aumentar learning rate: 0.0001 → 0.0002
- Aumentar epochs: 300 → 500
- Mais dados de treinamento (30+ min)

---

## 📈 Próximas Etapas

1. **Melhorar Qualidade:**
   - Treinar múltiplos modelos
   - Usar fine-tuning em modelos base melhores
   - Dados de treinamento diversificados

2. **Automação Completa:**
   - API integration com HeyGen
   - Webhook para triggers automáticos
   - Batch processing de múltiplos prompts

3. **Publicação:**
   - Criar playlist de vídeos
   - Publicar em YouTube/TikTok automaticamente
   - Analytics de performance

---

## 📞 Suporte

**Erros comuns:**
- Verifique logs em: `app/runtime/logs/`
- Veja eventos em: `http://localhost:3000/jobs`

**Arquivos Importantes:**
- Configuração: `app/backend/core/settings.py`
- Modelos treinados: `app/models/voices/spouse_voice/`
- Áudio gerado: `app/runtime/audio/output/`

---

**Boa sorte clonando a voz! 🎉**
