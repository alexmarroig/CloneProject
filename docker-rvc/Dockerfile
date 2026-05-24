FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy RVC from host
COPY ../. /rvc

WORKDIR /rvc

# Install RVC dependencies with Python 3.10 (more compatible with fairseq)
RUN pip install --no-cache-dir -r requirements.txt

# Expose API port
EXPOSE 8002

# Start RVC API server
CMD ["python", "-m", "uvicorn", "app.backend.routers.voice_engine:app", "--host", "0.0.0.0", "--port", "8002"]
