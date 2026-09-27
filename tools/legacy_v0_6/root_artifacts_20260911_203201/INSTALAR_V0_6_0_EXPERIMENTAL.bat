@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title NUCLEO IA PORTATIL - Instalar V0.6.0 Experimental
powershell -NoProfile -ExecutionPolicy Bypass -File ".\INSTALAR_V0_6_0_EXPERIMENTAL.ps1"
echo.
pause
endlocal
