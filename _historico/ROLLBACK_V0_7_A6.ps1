# NUCLEO IA PORTATIL - ROLLBACK V0.7 Fase 3 fatia 4 (alpha6) -> volta para alpha5
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Fail([string]$Message) {
    Write-Host ""; Write-Host "ERRO: $Message" -ForegroundColor Red; Write-Host ""; exit 1
}

Write-Host ""
Write-Host "============================================================================"
Write-Host "        NUCLEO IA PORTATIL - ROLLBACK V0.7 FASE 3 fatia 4 (alpha6)"
Write-Host "============================================================================"
Write-Host ""

$BackupRoot = Join-Path $Root "backup"
$Latest = Get-ChildItem -LiteralPath $BackupRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "pre_v0_7_a6_files_*" } |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $Latest) { Fail "Nenhum backup pre_v0_7_a6_files_* encontrado em $BackupRoot" }

Write-Host "Backup encontrado: $($Latest.FullName)"
$Answer = Read-Host "Reverter a fatia 4 (voltar ao alpha5)? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) { Write-Host "Cancelado."; exit 0 }

Write-Host ""
Write-Host "1/2 - Restaurando VERSION.json e removendo o tool novo..."
$verSrc = Join-Path $Latest.FullName "VERSION.json"
if (Test-Path -LiteralPath $verSrc) {
    Copy-Item -LiteralPath $verSrc -Destination (Join-Path $Root "VERSION.json") -Force
    $plVer = Join-Path $Root "payload\VERSION.json"
    if (Test-Path -LiteralPath (Split-Path -Parent $plVer)) { Copy-Item -LiteralPath $verSrc -Destination $plVer -Force }
    Write-Host "  restaurado: VERSION.json"
}
foreach ($Rel in @("tools\validar_modelo.py", "payload\tools\validar_modelo.py")) {
    $p = Join-Path $Root $Rel
    if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force; Write-Host "  removido: $Rel" }
}

Write-Host "2/2 - Concluindo..."
$State = Join-Path $Root "state\v0_7_a6_install.json"
if (Test-Path -LiteralPath $State) { Remove-Item -LiteralPath $State -Force }

Write-Host ""
Write-Host "ROLLBACK CONCLUIDO. Estado corrente: V0.7.0-alpha5."
Write-Host ""
