# NUCLEO IA PORTATIL - ROLLBACK V0.9 Escritor 360 (alpha2) -> volta para alpha1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Fail([string]$Message) {
    Write-Host ""; Write-Host "ERRO: $Message" -ForegroundColor Red; Write-Host ""; exit 1
}

Write-Host ""
Write-Host "        NUCLEO IA PORTATIL - ROLLBACK V0.9 ESCRITOR 360 (alpha2)"
Write-Host ""

$BackupRoot = Join-Path $Root "backup"
$Latest = Get-ChildItem -LiteralPath $BackupRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "pre_v0_9_a2_files_*" } |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $Latest) { Fail "Nenhum backup pre_v0_9_a2_files_* encontrado em $BackupRoot" }

Write-Host "Backup encontrado: $($Latest.FullName)"
$Answer = Read-Host "Reverter a fatia 2 (voltar ao alpha1)? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) { Write-Host "Cancelado."; exit 0 }

$verSrc = Join-Path $Latest.FullName "VERSION.json"
if (Test-Path -LiteralPath $verSrc) {
    Copy-Item -LiteralPath $verSrc -Destination (Join-Path $Root "VERSION.json") -Force
    $plVer = Join-Path $Root "payload\VERSION.json"
    if (Test-Path -LiteralPath (Split-Path -Parent $plVer)) { Copy-Item -LiteralPath $verSrc -Destination $plVer -Force }
    Write-Host "restaurado: VERSION.json"
}
foreach ($Rel in @("app\book\outline.py", "payload\app\book\outline.py", "OUTLINE.bat")) {
    $p = Join-Path $Root $Rel
    if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force; Write-Host "removido: $Rel" }
}
$State = Join-Path $Root "state\v0_9_a2_install.json"
if (Test-Path -LiteralPath $State) { Remove-Item -LiteralPath $State -Force }
Write-Host ""
Write-Host "ROLLBACK CONCLUIDO. Estado corrente: V0.9.0-alpha1."
Write-Host ""
