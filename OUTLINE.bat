@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
"runtime\python\python.exe" "app\book\outline.py" %*
pause

