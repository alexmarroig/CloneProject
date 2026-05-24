@echo off
REM Script para iniciar o Frontend do Voice Engine

echo.
echo ========================================
echo   Voice Engine - Frontend Startup
echo ========================================
echo.

cd /d "%~dp0"

echo Navegando para diretorio frontend...
cd app\frontend

echo.
echo Iniciando Next.js dev server...
echo Acesse: http://localhost:3000
echo.

npm run dev

pause
