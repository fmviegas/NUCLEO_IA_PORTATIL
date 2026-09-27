@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
"runtime\python\python.exe" "tools\validar_v0_9_22_final.py"
echo.
pause
