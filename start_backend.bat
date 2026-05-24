@echo off
REM Script para iniciar o Backend do Voice Engine

echo.
echo ========================================
echo   Voice Engine - Backend Startup
echo ========================================
echo.

cd /d "%~dp0"

echo Iniciando FastAPI server...
echo Acesse: http://127.0.0.1:8000
echo Health Check: http://127.0.0.1:8000/health
echo.

python -m uvicorn app.backend.api.main:app --reload --host 127.0.0.1 --port 8000

pause
