@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ROLLBACK_V0_9_A6.ps1"
echo.
pause
