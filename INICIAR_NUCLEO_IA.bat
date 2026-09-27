@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title NUCLEO IA PORTATIL V0.9.18

if not exist "runtime\python\python.exe" goto :runtime_error
if not exist "app\server.py" goto :app_error

"runtime\python\python.exe" "app\server.py"
set EXITCODE=%ERRORLEVEL%
if "%EXITCODE%"=="0" goto :success

echo.
echo O NUCLEO encerrou com codigo %EXITCODE%.
echo Consulte a pasta logs para detalhes.
echo.
pause
exit /b %EXITCODE%

:runtime_error
echo.
echo ERRO: runtime Python portatil nao encontrado.
echo.
pause
exit /b 2

:app_error
echo.
echo ERRO: app\server.py nao encontrado.
echo.
pause
exit /b 3

:success
endlocal
exit /b 0
