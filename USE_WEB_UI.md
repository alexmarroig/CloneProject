# 🎤 Use a Interface Web Para Converter

## Você já tem tudo pronto!

Seu projeto tem um **backend FastAPI** que pode fazer a conversão de voz diretamente pela web.

---

## 🚀 PASSO 1: Inicie o Backend

```bash
cd C:\Users\gaming\Desktop\Projetos\AI\Retrieval-based-Voice-Conversion-WebUI
python app/backend/api/main.py
```

Aguarde ver:
```
INFO:     Uvicorn running on http://0.0.0.0:5000
```

---

## 🌐 PASSO 2: Abra no Navegador

Acesse: http://localhost:5000

Você verá a interface web do projeto.

---

## 📤 PASSO 3: Converter Seu Áudio

1. Clique em "Voice Conversion" ou "RVC"
2. Upload do arquivo: `tts_temp.mp3`
3. Modelo: `esposa_voice`
4. Clique em "Convert"
5. Aguarde 3-5 minutos
6. Download do resultado

---

## ⚙️ Alternativa: Via API Direta

Se preferir via linha de comando:

```bash
curl -X POST http://localhost:5000/api/convert \
  -F "audio=@tts_temp.mp3" \
  -F "model=esposa_voice" \
  -F "f0_up_key=0" \
  -o reels_audio_esposa_voice.wav
```

---

## ✨ Resultado

Você receberá:
- Arquivo: `reels_audio_esposa_voice.wav`
- Com a voz da sua esposa!
- Pronto para reels

---

## 💡 Por Que Isso Funciona?

O backend já tem:
- ✅ RVC integrado
- ✅ Seu modelo carregado
- ✅ API pronta
- ✅ Interface web
- ✅ Sem problemas de compatibilidade

É a solução MAIS direta que você tem! 🎯
