@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ROLLBACK_V0_7_FINAL.ps1"
echo.
pause
