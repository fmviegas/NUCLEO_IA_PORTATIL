@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
"runtime\python\python.exe" "tools\calibrar_advanced.py" %*
echo.
pause