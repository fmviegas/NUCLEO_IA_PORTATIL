@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title NUCLEO IA PORTATIL - Hotfix V0.6.2.1

if not exist "runtime\python\python.exe" goto :runtime_error

"runtime\python\python.exe" "APLICAR_HOTFIX_V0_6_2_1.py"
goto :finish

:runtime_error
echo.
echo ERRO: runtime Python portatil nao encontrado.

:finish
echo.
pause
endlocal
