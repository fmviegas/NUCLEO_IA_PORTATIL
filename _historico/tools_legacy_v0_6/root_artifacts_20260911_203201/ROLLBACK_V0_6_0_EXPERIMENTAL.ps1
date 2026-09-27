# NUCLEO IA PORTATIL - ROLLBACK V0.6.0 EXPERIMENTAL
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$StatePath = Join-Path $Root "state\v0_6_0_install.json"

if (-not (Test-Path -LiteralPath $StatePath)) {
    Write-Host "Estado de instalacao V0.6.0 nao encontrado."
    exit 1
}

$State = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
$BackupDir = [string]$State.backup_dir

if (-not (Test-Path -LiteralPath $BackupDir)) {
    Write-Host "Backup da V0.5 nao encontrado:"
    Write-Host $BackupDir
    exit 2
}

Write-Host ""
Write-Host "Este rollback restaura o launcher e VERSION.json da V0.5."
$Answer = Read-Host "Continuar? [s/N]"
if ($Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) {
    Write-Host "Cancelado."
    exit 0
}

foreach ($Rel in @("INICIAR_NUCLEO_IA.bat","VERSION.json")) {
    $Source = Join-Path $BackupDir $Rel
    if (Test-Path -LiteralPath $Source) {
        Copy-Item -LiteralPath $Source -Destination (Join-Path $Root $Rel) -Force
    }
}

Write-Host ""
Write-Host "Rollback concluido."
Write-Host "Os arquivos experimentais foram mantidos, mas o launcher voltou para a V0.5."
