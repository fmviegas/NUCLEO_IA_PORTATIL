# NUCLEO IA PORTATIL - ROLLBACK V0.6.4
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$StatePath = Join-Path $Root "state\v0_6_4_install.json"

if (-not (Test-Path -LiteralPath $StatePath)) {
    Write-Host "Estado de instalacao V0.6.4 nao encontrado."
    exit 1
}

$State = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
$BackupDir = [string]$State.backup_dir

if (-not (Test-Path -LiteralPath $BackupDir)) {
    Write-Host "Backup anterior nao encontrado:"
    Write-Host $BackupDir
    exit 2
}

Write-Host ""
Write-Host "Este rollback restaura exatamente os arquivos anteriores a V0.6.4."
Write-Host "Perfis, historico, modelos e logs serao preservados."
$Answer = Read-Host "Continuar? [s/N]"
if ($Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) {
    Write-Host "Cancelado."
    exit 0
}

foreach ($Rel in @(
    "INICIAR_NUCLEO_IA.bat",
    "VERSION.json",
    "app\server.py",
    "app\engine_manager.py",
    "app\maintenance_manager.py",
    "app\calibration_manager.py",
    "app\autotune.py",
    "app\benchmark.py",
    "app\sessions.py",
    "ui\index.html",
    "ui\app.css",
    "ui\app.js"
)) {
    $Source = Join-Path $BackupDir $Rel
    if (Test-Path -LiteralPath $Source) {
        Copy-Item -LiteralPath $Source -Destination (Join-Path $Root $Rel) -Force
    }
}

Write-Host ""
Write-Host "Rollback concluido."
