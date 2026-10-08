@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
rem Baixa modelos pesados do catalogo (Hugging Face) e confere o SHA256.
"runtime\python\python.exe" "tools\baixar_modelos.py" %*
echo.
pause
