@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
rem Calibra AVANCADO (livros), CODIGO e VISAO com o MELHOR modelo baixado que cabe nesta maquina.
"runtime\python\python.exe" "tools\calibrar_advanced.py" --todos %*
echo.
pause
