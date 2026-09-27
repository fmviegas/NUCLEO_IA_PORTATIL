# NUCLEO IA PORTATIL - ROLLBACK V0.7 Fase 3 fatia 3 (alpha5) -> volta para alpha4
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Fail([string]$Message) {
    Write-Host ""; Write-Host "ERRO: $Message" -ForegroundColor Red; Write-Host ""; exit 1
}

Write-Host ""
Write-Host "============================================================================"
Write-Host "        NUCLEO IA PORTATIL - ROLLBACK V0.7 FASE 3 fatia 3 (alpha5)"
Write-Host "============================================================================"
Write-Host ""

$BackupRoot = Join-Path $Root "backup"
$Latest = Get-ChildItem -LiteralPath $BackupRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "pre_v0_7_a5_files_*" } |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $Latest) { Fail "Nenhum backup pre_v0_7_a5_files_* encontrado em $BackupRoot" }

Write-Host "Backup encontrado: $($Latest.FullName)"
$Answer = Read-Host "Reverter a fatia 3 (voltar ao alpha4)? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) { Write-Host "Cancelado."; exit 0 }

Write-Host ""
Write-Host "1/2 - Restaurando arquivos (raiz e payload)..."
foreach ($Rel in @("VERSION.json", "app\engine_manager.py")) {
    $Source = Join-Path $Latest.FullName $Rel
    if (Test-Path -LiteralPath $Source) {
        Copy-Item -LiteralPath $Source -Destination (Join-Path $Root $Rel) -Force
        $plDst = Join-Path (Join-Path $Root "payload") $Rel
        if (Test-Path -LiteralPath (Split-Path -Parent $plDst)) {
            Copy-Item -LiteralPath $Source -Destination $plDst -Force
        }
        Write-Host "  restaurado: $Rel"
    }
}

Write-Host "2/2 - Validando Python..."
$Python = Join-Path $Root "runtime\python\python.exe"
& $Python -m py_compile (Join-Path $Root "app\engine_manager.py")
if ($LASTEXITCODE -ne 0) { Fail "Validacao Python falhou apos rollback." }

$State = Join-Path $Root "state\v0_7_a5_install.json"
if (Test-Path -LiteralPath $State) { Remove-Item -LiteralPath $State -Force }

Write-Host ""
Write-Host "ROLLBACK CONCLUIDO. Estado corrente: V0.7.0-alpha4."
Write-Host ""
