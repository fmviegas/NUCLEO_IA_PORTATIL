# NUCLEO IA PORTATIL - ROLLBACK V0.6.1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$StatePath = Join-Path $Root "state\v0_6_1_install.json"

if (-not (Test-Path -LiteralPath $StatePath)) {
    Write-Host "Estado de instalação V0.6.1 não encontrado."
    exit 1
}

$State = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
$BackupDir = [string]$State.backup_dir

if (-not (Test-Path -LiteralPath $BackupDir)) {
    Write-Host "Backup da V0.6.0 não encontrado:"
    Write-Host $BackupDir
    exit 2
}

Write-Host ""
Write-Host "Este rollback restaura os arquivos da interface V0.6.0."
Write-Host "A pasta sessions será PRESERVADA."
$Answer = Read-Host "Continuar? [s/N]"
if ($Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) {
    Write-Host "Cancelado."
    exit 0
}

foreach ($Rel in @(
    "VERSION.json",
    "app\server.py",
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
Write-Host "Rollback concluído."
Write-Host "O histórico local foi preservado em sessions\."
