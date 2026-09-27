# NUCLEO IA PORTATIL - ROLLBACK V0.9 Escritor 360 (alpha1) -> volta para V0.7 FINAL
# Remove os arquivos NOVOS (nao existiam antes). NAO toca em workspace/livros do usuario.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Fail([string]$Message) {
    Write-Host ""; Write-Host "ERRO: $Message" -ForegroundColor Red; Write-Host ""; exit 1
}

Write-Host ""
Write-Host "============================================================================"
Write-Host "        NUCLEO IA PORTATIL - ROLLBACK V0.9 ESCRITOR 360 (alpha1)"
Write-Host "============================================================================"
Write-Host ""

$BackupRoot = Join-Path $Root "backup"
$Latest = Get-ChildItem -LiteralPath $BackupRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "pre_v0_9_a1_files_*" } |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $Latest) { Fail "Nenhum backup pre_v0_9_a1_files_* encontrado em $BackupRoot" }

Write-Host "Backup encontrado: $($Latest.FullName)"
Write-Host "Obs: seus livros em workspace\livros NAO serao tocados." -ForegroundColor Yellow
$Answer = Read-Host "Reverter a fatia 1 do Escritor 360 (voltar a V0.7 FINAL)? [S/n]"
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
foreach ($Rel in @("app\book", "config\personas",
                   "payload\app\book", "payload\config\personas",
                   "CRIAR_LIVRO.bat", "PLANO_LIVRO.bat", "HUMANIZAR.bat")) {
    $p = Join-Path $Root $Rel
    if (Test-Path -LiteralPath $p) {
        Remove-Item -LiteralPath $p -Recurse -Force
        Write-Host "  removido: $Rel"
    }
}

Write-Host "2/2 - Concluindo..."
$State = Join-Path $Root "state\v0_9_a1_install.json"
if (Test-Path -LiteralPath $State) { Remove-Item -LiteralPath $State -Force }

Write-Host ""
Write-Host "ROLLBACK CONCLUIDO. Estado corrente: V0.7 FINAL."
Write-Host "Seus livros em workspace\livros permanecem intactos."
Write-Host ""
