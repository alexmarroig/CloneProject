# Voice Engine App

## Backend

```bash
pip install -r app/backend/requirements.txt
uvicorn app.backend.api.main:app --reload
```

## Frontend

```bash
cd app/frontend
npm install
npm run dev
```

## Worker environments

Create isolated Python environments:

- `app/runtime/envs/xtts`
- `app/runtime/envs/rvc`

The XTTS worker needs Coqui TTS installed.
The RVC worker should reuse the dependency set compatible with this repository.

## XTTS speaker reference

Set `VOICE_ENGINE_XTTS_SPEAKER_WAV` or place `speaker.wav` inside `app/models/xtts/`.

## API

- `POST /generate_voice`
- `POST /train_voice`
- `GET /voices`
- `GET /jobs/{job_id}`
- `GET /health`
