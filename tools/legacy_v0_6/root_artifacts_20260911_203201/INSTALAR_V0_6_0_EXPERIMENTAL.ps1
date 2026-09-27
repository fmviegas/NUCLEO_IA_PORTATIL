# NUCLEO IA PORTATIL - INSTALADOR V0.6.0 EXPERIMENTAL
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Payload = Join-Path $Root "payload"

function Fail([string]$Message) {
    Write-Host ""
    Write-Host "ERRO: $Message" -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "============================================================================"
Write-Host "        NUCLEO IA PORTATIL - V0.6.0 EXPERIMENTAL"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Minimalismo funcional: HTML/CSS/JavaScript puro + Python local."
Write-Host "Este patch NAO altera modelos, perfis ou calibracao V0.5."
Write-Host ""

foreach ($Path in @(
    (Join-Path $Root "runtime\python\python.exe"),
    (Join-Path $Root "app\hardware.py"),
    (Join-Path $Root "profiles\machines"),
    (Join-Path $Root "engine\windows\cpu\llama-server.exe"),
    (Join-Path $Root "engine\windows\cuda\llama-server.exe"),
    (Join-Path $Root "models\Qwen3-4B-Q4_K_M.gguf"),
    (Join-Path $Root "models\Qwen3-8B-Q4_K_M.gguf"),
    $Payload
)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        Fail "Componente necessario ausente: $Path"
    }
}

$Answer = Read-Host "Instalar a interface experimental agora? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) {
    Write-Host "Cancelado."
    exit 0
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root ("backup\pre_v0_6_0_" + $Stamp)
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

Write-Host ""
Write-Host "1/4 - Criando backup pequeno da V0.5..."
foreach ($Rel in @("INICIAR_NUCLEO_IA.bat","VERSION.json")) {
    $Source = Join-Path $Root $Rel
    if (Test-Path -LiteralPath $Source) {
        Copy-Item -LiteralPath $Source -Destination (Join-Path $BackupDir $Rel) -Force
    }
}

Write-Host "2/4 - Instalando backend e interface..."
Get-ChildItem -LiteralPath $Payload -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $Root -Recurse -Force
}

Write-Host "3/4 - Validando Python..."
$Python = Join-Path $Root "runtime\python\python.exe"
& $Python -m py_compile `
    (Join-Path $Root "app\server.py") `
    (Join-Path $Root "app\engine_manager.py")
if ($LASTEXITCODE -ne 0) {
    Fail "Falha na validacao dos modulos Python."
}

Write-Host "4/4 - Gravando estado da instalacao..."
$StateDir = Join-Path $Root "state"
New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
$State = [PSCustomObject]@{
    product = "NUCLEO IA PORTATIL"
    version = "0.6.0-experimental"
    installed_at = (Get-Date).ToString("o")
    backup_dir = $BackupDir
}
$State | ConvertTo-Json -Depth 4 |
    Set-Content (Join-Path $StateDir "v0_6_0_install.json") -Encoding UTF8

Write-Host ""
Write-Host "============================================================================"
Write-Host "INSTALACAO V0.6.0 EXPERIMENTAL CONCLUIDA"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Agora execute:"
Write-Host "  $Root\INICIAR_NUCLEO_IA.bat"
Write-Host ""
Write-Host "Rollback disponivel em:"
Write-Host "  ROLLBACK_V0_6_0_EXPERIMENTAL.bat"
