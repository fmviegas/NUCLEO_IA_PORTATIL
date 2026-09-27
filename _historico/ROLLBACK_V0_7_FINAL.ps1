# NUCLEO IA PORTATIL - ROLLBACK DA CONSOLIDACAO V0.7 FINAL
# Restaura VERSION.json anterior. NAO altera codigo do app (fica na base alpha6).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Fail([string]$Message) {
    Write-Host ""; Write-Host "ERRO: $Message" -ForegroundColor Red; Write-Host ""; exit 1
}

Write-Host ""
Write-Host "============================================================================"
Write-Host "        NUCLEO IA PORTATIL - ROLLBACK V0.7 FINAL"
Write-Host "============================================================================"
Write-Host ""

$BackupRoot = Join-Path $Root "backup"
$Latest = Get-ChildItem -LiteralPath $BackupRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "pre_v0_7_final_*" } |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $Latest) { Fail "Nenhum backup pre_v0_7_final_* encontrado em $BackupRoot" }

Write-Host "Backup encontrado: $($Latest.FullName)"
$Answer = Read-Host "Reverter a consolidacao V0.7 FINAL? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) { Write-Host "Cancelado."; exit 0 }

Write-Host ""
Write-Host "1/2 - Restaurando VERSION.json anterior..."
$Src = Join-Path $Latest.FullName "VERSION.json"
if (Test-Path -LiteralPath $Src) {
    Copy-Item -LiteralPath $Src -Destination (Join-Path $Root "VERSION.json") -Force
    $plVer = Join-Path $Root "payload\VERSION.json"
    if (Test-Path -LiteralPath (Split-Path -Parent $plVer)) { Copy-Item -LiteralPath $Src -Destination $plVer -Force }
    Write-Host "  restaurado: VERSION.json"
} else {
    Write-Host "  (sem VERSION.json no backup; mantido o atual)" -ForegroundColor Yellow
}

Write-Host "2/2 - Removendo marcador de consolidacao..."
$State = Join-Path $Root "state\v0_7_final_install.json"
if (Test-Path -LiteralPath $State) { Remove-Item -LiteralPath $State -Force }

Write-Host ""
Write-Host "ROLLBACK CONCLUIDO. VERSION voltou ao estado anterior a consolidacao."
Write-Host "Observacao: o codigo do app permanece na base alpha6 (nao e alterado aqui)."
Write-Host ""
