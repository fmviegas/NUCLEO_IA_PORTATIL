@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title NUCLEO IA PORTATIL - Rollback Hotfix V0.6.2.1
"runtime\python\python.exe" "ROLLBACK_HOTFIX_V0_6_2_1.py"
echo.
pause
endlocal
