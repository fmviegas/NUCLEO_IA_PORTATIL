@echo off
setlocal
cd /d "%~dp0\.."
chcp 65001 >nul
title NUCLEO IA PORTATIL - Reparo CUDA
powershell -NoProfile -ExecutionPolicy Bypass -File ".\tools\reparar_motor_cuda.ps1"
echo.
pause
endlocal
