# NUCLEO IA PORTATIL - ROLLBACK DO HOTFIX V0.6.5.3
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
Write-Host "        NUCLEO IA PORTATIL - ROLLBACK V0.6.5.3"
Write-Host "============================================================================"
Write-Host ""

$BackupRoot = Join-Path $Root "backup"
$Latest = Get-ChildItem -LiteralPath $BackupRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "pre_v0_6_5_3_files_*" } |
    Sort-Object Name -Descending | Select-Object -First 1

if (-not $Latest) {
    Fail "Nenhum backup pre_v0_6_5_3_files_* encontrado em $BackupRoot"
}

Write-Host "Backup encontrado: $($Latest.FullName)"
$Answer = Read-Host "Reverter para o estado anterior a V0.6.5.3? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) {
    Write-Host "Cancelado."
    exit 0
}

Write-Host ""
Write-Host "1/2 - Restaurando arquivos..."
foreach ($Rel in @(
    "VERSION.json",
    "app\engine_manager.py"
)) {
    $Source = Join-Path $Latest.FullName $Rel
    $Dest = Join-Path $Root $Rel
    if (Test-Path -LiteralPath $Source) {
        Copy-Item -LiteralPath $Source -Destination $Dest -Force
        Write-Host "  restaurado: $Rel"
    }
}

Write-Host "2/2 - Validando Python..."
$Python = Join-Path $Root "runtime\python\python.exe"
& $Python -m py_compile (Join-Path $Root "app\engine_manager.py")
if ($LASTEXITCODE -ne 0) {
    Fail "Validacao Python falhou apos rollback."
}

$State = Join-Path $Root "state\v0_6_5_3_install.json"
if (Test-Path -LiteralPath $State) {
    Remove-Item -LiteralPath $State -Force
}

Write-Host ""
Write-Host "ROLLBACK CONCLUIDO. NUCLEO voltou ao estado anterior a V0.6.5.3."
Write-Host ""
