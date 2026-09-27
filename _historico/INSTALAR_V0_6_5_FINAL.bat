@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALAR_V0_6_5_FINAL.ps1"
echo.
pause
