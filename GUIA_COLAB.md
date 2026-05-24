# 🎤 Guia: Converter Áudio no Google Colab

## Por que Colab?

O Google Colab tem:
- ✅ GPU GRÁTIS (100x mais rápido que CPU)
- ✅ RVC com todas as dependências funcionando
- ✅ Sem problemas de compatibilidade
- ✅ Resultado em 2-3 minutos

---

## 📋 Passo a Passo

### PASSO 1: Prepare os Arquivos Locais

Você já tem:
- ✅ `assets/weights/esposa_voice.pth` (seu modelo treinado)
- ✅ `tts_temp.mp3` (seu áudio em português)

Verifique que existem:
```bash
ls -lh assets/weights/esposa_voice.pth
ls -lh tts_temp.mp3
```

---

### PASSO 2: Abra o Google Colab

1. Acesse: https://colab.research.google.com/
2. Clique em "Novo notebook"
3. Renomeie para: "RVC Voice Conversion"

---

### PASSO 3: Copie e Cole o Código

Copie todo o código de `colab_rvc_conversion.py` e cole no primeiro cell do Colab.

**OU** Cole este código resumido:

```python
# CELL 1: Setup
!pip install -q torch librosa soundfile fairseq
!git clone -q https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git RVC
import os
os.chdir("/content/RVC")
print("[OK] Setup complete")
```

---

### PASSO 4: Execute Cell por Cell

Para cada cell:
1. Clique no código
2. Pressione `Shift + Enter` ou clique o botão de play

#### Cell 1: Setup (30 segundos)
```python
!pip install -q torch librosa soundfile fairseq numpy scipy pydub
!git clone -q https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git RVC
import os
os.chdir("/content/RVC")
```

#### Cell 2: Upload Files (30 segundos)
```python
from google.colab import files
from pathlib import Path

print("1. Upload esposa_voice.pth")
uploaded = files.upload()
model_file = list(uploaded.keys())[0]

print("2. Upload tts_temp.mp3")
uploaded = files.upload()
audio_file = list(uploaded.keys())[0]

import shutil
Path("assets/weights").mkdir(parents=True, exist_ok=True)
shutil.copy(f"/content/{model_file}", "assets/weights/esposa_voice.pth")
shutil.copy(f"/content/{audio_file}", audio_file)

print(f"[OK] Files ready")
```

#### Cell 3: Run Conversion (2-3 minutos)
```python
import sys
sys.path.insert(0, "/content/RVC")

from infer.modules.vc.modules import VC
import soundfile as sf
import librosa
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device}")

vc = VC(tgt_sr=40000, device=device, is_half=True)
vc.get_vc("esposa_voice.pth", 0, device)

audio_data, sr = librosa.load("tts_temp.mp3", sr=40000)
print(f"Audio loaded: {len(audio_data)} samples @ {sr}Hz")

output_audio, _ = vc.infer(
    speaker_id=0,
    audio_data=audio_data,
    times=0,
    top_k=5,
    top_p=1,
    temperature=1
)

output = output_audio[0, 0].data.cpu().numpy()
if output.max() > 0:
    output = output / output.max() * 0.95

sf.write("reels_audio_esposa_voice.wav", output, sr)
print("[OK] Conversion complete!")
```

#### Cell 4: Download (10 segundos)
```python
from google.colab import files
files.download("reels_audio_esposa_voice.wav")
print("[OK] Download started!")
```

---

## ✅ Resultado

Você receberá um arquivo:
- **Nome**: `reels_audio_esposa_voice.wav`
- **Duração**: ~49 segundos
- **Voz**: DA SUA ESPOSA (via modelo RVC treinado)
- **Pronto para**: Instagram Reels, TikTok, YouTube Shorts

---

## 🎯 Timeline

| Ação | Tempo |
|------|-------|
| Setup + Instalações | 1-2 min |
| Upload de arquivos | 30 seg |
| Voice Conversion | 2-3 min |
| Download | 30 seg |
| **TOTAL** | **~5-6 min** |

---

## 🆘 Se Der Erro

### "Module not found: fairseq"
```python
!pip install --upgrade fairseq
```

### "CUDA out of memory"
```python
device = "cpu"  # Use CPU instead
```

### "Audio file not found"
- Verifique o nome exato do arquivo
- Re-upload se necessário

---

## 📝 Notas Importantes

1. **GPU Gratuita**: Colab fornece GPU grátis (~T4)
2. **Velocidade**: Com GPU: 2-3 min. Com CPU: 10-15 min
3. **Limite**: Cada sessão tem 12 horas
4. **Reiniciar**: Se desligar, inicie novo notebook

---

## ✨ Resultado Final

Depois que o download terminar:
1. Você terá o arquivo `.wav` com a voz da sua esposa
2. Abra em seu editor de vídeos
3. Sincronize com video/imagens
4. Poste nos reels!

---

**Tempo Total: ~5 minutos no Colab**

Muito mais rápido que CPU e SEM problemas de compatibilidade! 🚀
