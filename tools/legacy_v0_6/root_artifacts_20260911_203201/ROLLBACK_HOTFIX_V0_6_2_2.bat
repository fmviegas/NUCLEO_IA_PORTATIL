@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title NUCLEO IA PORTATIL - Rollback Hotfix V0.6.2.2
"runtime\python\python.exe" "ROLLBACK_HOTFIX_V0_6_2_2.py"
echo.
pause
endlocal
