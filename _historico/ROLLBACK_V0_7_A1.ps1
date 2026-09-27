# NUCLEO IA PORTATIL - ROLLBACK V0.7 Fase 1 (alpha1) -> volta para V0.6.5 FINAL
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Fail([string]$Message) {
    Write-Host ""
    Write-Host "ERRO: $Message" -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "============================================================================"
Write-Host "        NUCLEO IA PORTATIL - ROLLBACK V0.7 FASE 1 (alpha1)"
Write-Host "============================================================================"
Write-Host ""

$BackupRoot = Join-Path $Root "backup"
$Latest = Get-ChildItem -LiteralPath $BackupRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "pre_v0_7_a1_files_*" } |
    Sort-Object Name -Descending | Select-Object -First 1

if (-not $Latest) {
    Fail "Nenhum backup pre_v0_7_a1_files_* encontrado em $BackupRoot"
}

Write-Host "Backup encontrado: $($Latest.FullName)"
$Answer = Read-Host "Reverter para o estado anterior (V0.6.5 FINAL)? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) {
    Write-Host "Cancelado."
    exit 0
}

Write-Host ""
Write-Host "1/2 - Restaurando arquivos..."
foreach ($Rel in @(
    "VERSION.json",
    "app\hardware.py",
    "app\autotune.py",
    "app\engine_manager.py"
)) {
    $Source = Join-Path $Latest.FullName $Rel
    $Dest = Join-Path $Root $Rel
    if (Test-Path -LiteralPath $Source) {
        Copy-Item -LiteralPath $Source -Destination $Dest -Force
        Write-Host "  restaurado: $Rel"
    }
}

# Reverte tambem a copia do payload, para o instalador nao reaplicar o alpha.
$plOrig = $Latest.FullName
foreach ($Rel in @("app\hardware.py","app\autotune.py","app\engine_manager.py","VERSION.json")) {
    $src = Join-Path $plOrig $Rel
    $dst = Join-Path (Join-Path $Root "payload") $Rel
    if ((Test-Path -LiteralPath $src) -and (Test-Path -LiteralPath (Split-Path -Parent $dst))) {
        Copy-Item -LiteralPath $src -Destination $dst -Force
    }
}

Write-Host "2/2 - Validando Python..."
$Python = Join-Path $Root "runtime\python\python.exe"
& $Python -m py_compile `
    (Join-Path $Root "app\hardware.py") `
    (Join-Path $Root "app\autotune.py") `
    (Join-Path $Root "app\engine_manager.py")
if ($LASTEXITCODE -ne 0) {
    Fail "Validacao Python falhou apos rollback."
}

$State = Join-Path $Root "state\v0_7_a1_install.json"
if (Test-Path -LiteralPath $State) { Remove-Item -LiteralPath $State -Force }

Write-Host ""
Write-Host "ROLLBACK CONCLUIDO. Estado corrente: V0.6.5 FINAL."
Write-Host ""
