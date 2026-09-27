@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
echo ============================================================
echo   MONTAR PORTATIL - NUCLEO IA PORTATIL
echo   Copia so o essencial de operacao para um pendrive.
echo   IMPORTANTE: o pendrive deve estar em exFAT ou NTFS (NAO FAT32).
echo ============================================================
echo.
set /p DRIVE="Letra do pendrive (ex: G): "
if "%DRIVE%"=="" (echo Nenhuma letra informada. Cancelado.& pause & exit /b 1)
echo.
echo Modelos: all = 4B+8B+30B (~19.5GB) ^| fast = 4B+8B (~9GB) ^| min = so 4B (~4.6GB) ^| none
set /p TIER="Modelos [all/fast/min/none] (Enter=all): "
if "%TIER%"=="" set TIER=all
echo.
echo Simulando primeiro (dry-run)...
"runtime\python\python.exe" "tools\montar_portatil.py" --dest "%DRIVE%:\NUCLEO_IA_PORTATIL" --modelos %TIER% --dry-run
echo.
set /p GO="Prosseguir com a copia REAL? [S/n]: "
if /I not "%GO%"=="S" if not "%GO%"=="" (echo Cancelado.& pause & exit /b 0)
"runtime\python\python.exe" "tools\montar_portatil.py" --dest "%DRIVE%:\NUCLEO_IA_PORTATIL" --modelos %TIER%
echo.
pause
