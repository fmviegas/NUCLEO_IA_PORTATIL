@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title NUCLEO IA PORTATIL - Instalar V0.6.1
powershell -NoProfile -ExecutionPolicy Bypass -File ".\INSTALAR_V0_6_1.ps1"
echo.
pause
endlocal
