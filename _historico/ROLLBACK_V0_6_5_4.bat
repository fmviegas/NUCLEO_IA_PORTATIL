@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ROLLBACK_V0_6_5_4.ps1"
echo.
pause
