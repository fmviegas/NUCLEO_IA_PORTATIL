# NUCLEO IA PORTATIL - ROLLBACK V0.7 Fase 3 fatia 1 (alpha3) -> volta para alpha2
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Fail([string]$Message) {
    Write-Host ""; Write-Host "ERRO: $Message" -ForegroundColor Red; Write-Host ""; exit 1
}

Write-Host ""
Write-Host "============================================================================"
Write-Host "        NUCLEO IA PORTATIL - ROLLBACK V0.7 FASE 3 fatia 1 (alpha3)"
Write-Host "============================================================================"
Write-Host ""

$BackupRoot = Join-Path $Root "backup"
$Latest = Get-ChildItem -LiteralPath $BackupRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "pre_v0_7_a3_files_*" } |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $Latest) { Fail "Nenhum backup pre_v0_7_a3_files_* encontrado em $BackupRoot" }

Write-Host "Backup encontrado: $($Latest.FullName)"
$Answer = Read-Host "Reverter a fatia 1 do catalogo (voltar ao alpha2)? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) { Write-Host "Cancelado."; exit 0 }

Write-Host ""
Write-Host "1/2 - Restaurando VERSION.json e removendo arquivos novos..."
$verSrc = Join-Path $Latest.FullName "VERSION.json"
if (Test-Path -LiteralPath $verSrc) {
    Copy-Item -LiteralPath $verSrc -Destination (Join-Path $Root "VERSION.json") -Force
    $plVer = Join-Path $Root "payload\VERSION.json"
    if (Test-Path -LiteralPath (Split-Path -Parent $plVer)) { Copy-Item -LiteralPath $verSrc -Destination $plVer -Force }
    Write-Host "  restaurado: VERSION.json"
}
# catalog.py e models_registry.json eram NOVOS -> remover da raiz E do payload
foreach ($Rel in @("app\catalog.py", "config\models_registry.json",
                   "payload\app\catalog.py", "payload\config\models_registry.json")) {
    $p = Join-Path $Root $Rel
    if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force; Write-Host "  removido: $Rel" }
}

Write-Host "2/2 - Concluindo..."
$State = Join-Path $Root "state\v0_7_a3_install.json"
if (Test-Path -LiteralPath $State) { Remove-Item -LiteralPath $State -Force }

Write-Host ""
Write-Host "ROLLBACK CONCLUIDO. Estado corrente: V0.7.0-alpha2."
Write-Host ""
