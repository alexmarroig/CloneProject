@echo off
REM Script para iniciar Backend + Frontend do Voice Engine

echo.
echo ============================================================
echo   Voice Engine - Full Startup (Backend + Frontend)
echo ============================================================
echo.

cd /d "%~dp0"

echo.
echo [1/2] Iniciando Backend na porta 8000...
echo       Health Check: http://127.0.0.1:8000/health
start "Voice Engine Backend" cmd /k python -m uvicorn app.backend.api.main:app --reload --host 127.0.0.1 --port 8000

echo.
echo [2/2] Iniciando Frontend na porta 3000...
echo       Interface Web: http://localhost:3000
timeout /t 3 /nobreak
start "Voice Engine Frontend" cmd /k cd app\frontend && npm run dev

echo.
echo ============================================================
echo Sistema iniciado!
echo.
echo Frontend:  http://localhost:3000
echo Backend:   http://127.0.0.1:8000
echo Health:    http://127.0.0.1:8000/health
echo.
echo Feche as janelas de comando para parar o sistema.
echo ============================================================
echo.

pause
