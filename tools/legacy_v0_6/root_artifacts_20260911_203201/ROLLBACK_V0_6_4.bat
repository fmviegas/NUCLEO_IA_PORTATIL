@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title NUCLEO IA PORTATIL - Rollback V0.6.4
powershell -NoProfile -ExecutionPolicy Bypass -File ".\ROLLBACK_V0_6_4.ps1"
echo.
pause
endlocal
