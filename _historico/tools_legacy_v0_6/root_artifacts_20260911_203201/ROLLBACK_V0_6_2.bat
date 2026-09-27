@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title NUCLEO IA PORTATIL - Rollback V0.6.2
powershell -NoProfile -ExecutionPolicy Bypass -File ".\ROLLBACK_V0_6_2.ps1"
echo.
pause
endlocal
