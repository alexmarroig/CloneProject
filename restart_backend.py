import subprocess
import time
import os
import sys

# Kill existing uvicorn processes
os.system("taskkill /IM python.exe /F 2>nul")
time.sleep(2)

# Change to project directory
os.chdir(r"C:\Users\gaming\Desktop\Projetos\AI\Retrieval-based-Voice-Conversion-WebUI")

# Clear Python cache
for root, dirs, files in os.walk('.'):
    if '__pycache__' in dirs:
        import shutil
        shutil.rmtree(os.path.join(root, '__pycache__'), ignore_errors=True)

# Start new backend
subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.backend.api.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"]
)

time.sleep(5)
print("Backend restarted")
