# NUCLEO IA PORTATIL - ROLLBACK V0.6.2
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$StatePath = Join-Path $Root "state\v0_6_2_install.json"

if (-not (Test-Path -LiteralPath $StatePath)) {
    Write-Host "Estado de instalação V0.6.2 não encontrado."
    exit 1
}

$State = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
$BackupDir = [string]$State.backup_dir

if (-not (Test-Path -LiteralPath $BackupDir)) {
    Write-Host "Backup da V0.6.1 não encontrado:"
    Write-Host $BackupDir
    exit 2
}

Write-Host ""
Write-Host "Este rollback restaura a interface V0.6.1."
Write-Host "Perfis, histórico e resultados de calibração serão preservados."
$Answer = Read-Host "Continuar? [s/N]"
if ($Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) {
    Write-Host "Cancelado."
    exit 0
}

foreach ($Rel in @(
    "VERSION.json",
    "app\server.py",
    "app\engine_manager.py",
    "ui\index.html",
    "ui\app.css",
    "ui\app.js"
)) {
    $Source = Join-Path $BackupDir $Rel
    if (Test-Path -LiteralPath $Source) {
        Copy-Item -LiteralPath $Source -Destination (Join-Path $Root $Rel) -Force
    }
}

$CalibrationManager = Join-Path $Root "app\calibration_manager.py"
if (Test-Path -LiteralPath $CalibrationManager) {
    Remove-Item -LiteralPath $CalibrationManager -Force
}

Write-Host ""
Write-Host "Rollback concluído."
Write-Host "sessions\ e profiles\machines\ foram preservados."
