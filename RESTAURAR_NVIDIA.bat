@echo off
setlocal
cd /d "%~dp0"
if exist "state\SIMULATE_NO_NVIDIA" del /f /q "state\SIMULATE_NO_NVIDIA"
echo Simulacao DESATIVADA (NVIDIA/CUDA normal). Reinicie o motor ou reabra o NUCLEO.
pause
