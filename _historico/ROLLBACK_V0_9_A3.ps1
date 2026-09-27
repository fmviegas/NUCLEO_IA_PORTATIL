# NUCLEO IA PORTATIL - ROLLBACK V0.9 (alpha3) -> volta para alpha2
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Fail([string]$Message) {
    Write-Host ""; Write-Host "ERRO: $Message" -ForegroundColor Red; Write-Host ""; exit 1
}

$BackupRoot = Join-Path $Root "backup"
$Latest = Get-ChildItem -LiteralPath $BackupRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "pre_v0_9_a3_files_*" } |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $Latest) { Fail "Nenhum backup pre_v0_9_a3_files_* encontrado." }

Write-Host "Backup: $($Latest.FullName)"
$Answer = Read-Host "Reverter a fatia 2.1 (voltar ao alpha2)? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) { Write-Host "Cancelado."; exit 0 }

foreach ($Rel in @("VERSION.json", "app\book\outline.py")) {
    $src = Join-Path $Latest.FullName $Rel
    if (Test-Path -LiteralPath $src) {
        Copy-Item -LiteralPath $src -Destination (Join-Path $Root $Rel) -Force
        $plDst = Join-Path (Join-Path $Root "payload") $Rel
        if (Test-Path -LiteralPath (Split-Path -Parent $plDst)) { Copy-Item -LiteralPath $src -Destination $plDst -Force }
        Write-Host "restaurado: $Rel"
    }
}
$Python = Join-Path $Root "runtime\python\python.exe"
& $Python -m py_compile (Join-Path $Root "app\book\outline.py")
if ($LASTEXITCODE -ne 0) { Fail "Compile falhou apos rollback." }
$State = Join-Path $Root "state\v0_9_a3_install.json"
if (Test-Path -LiteralPath $State) { Remove-Item -LiteralPath $State -Force }
Write-Host ""
Write-Host "ROLLBACK CONCLUIDO. Estado corrente: V0.9.0-alpha2."
Write-Host ""
