# NUCLEO IA PORTATIL - ROLLBACK V0.6.3
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$StatePath = Join-Path $Root "state\v0_6_3_install.json"

if (-not (Test-Path -LiteralPath $StatePath)) {
    Write-Host "Estado de instalacao V0.6.3 nao encontrado."
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
Write-Host "Este rollback restaura a interface anterior."
Write-Host "Perfis, historico, calibracao e backups de motores serao preservados."
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

$Maintenance = Join-Path $Root "app\maintenance_manager.py"
if (Test-Path -LiteralPath $Maintenance) {
    Remove-Item -LiteralPath $Maintenance -Force
}

Write-Host ""
Write-Host "Rollback concluido."
