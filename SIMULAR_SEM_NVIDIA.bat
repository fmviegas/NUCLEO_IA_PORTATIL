@echo off
setlocal
cd /d "%~dp0"
if not exist "state" mkdir "state"
break > "state\SIMULATE_NO_NVIDIA"
echo Simulacao SEM NVIDIA ATIVADA. Reinicie o motor (Manutencao) ou reabra o NUCLEO.
echo Para restaurar: RESTAURAR_NVIDIA.bat
pause
