FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and server code
COPY requirements-xtts.txt .
COPY xtts_server.py .

# Install Python packages (CPU only - no CUDA)
RUN pip install --no-cache-dir -r requirements-xtts.txt

# Patch for isin_mps_friendly missing in transformers
RUN python3 << 'PATCH_EOF'
import pathlib
file = pathlib.Path("/usr/local/lib/python3.11/site-packages/TTS/tts/layers/tortoise/autoregressive.py")
content = file.read_text()
old = "from transformers.pytorch_utils import isin_mps_friendly as isin"
new = """try:
    from transformers.pytorch_utils import isin_mps_friendly as isin
except ImportError:
    import torch
    isin = torch.isin"""
if old in content:
    file.write_text(content.replace(old, new))
    print("✓ Patched autoregressive.py")
else:
    print("⚠ File already patched or not found")
PATCH_EOF

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8001

# Run the XTTS server
CMD ["python", "-m", "uvicorn", "xtts_server:app", "--host", "0.0.0.0", "--port", "8001"]
