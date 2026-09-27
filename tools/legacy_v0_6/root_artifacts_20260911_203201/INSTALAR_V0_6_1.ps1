# NUCLEO IA PORTATIL - INSTALADOR V0.6.1
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
Write-Host "             NUCLEO IA PORTATIL - V0.6.1"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Sessões e Histórico Local"
Write-Host "JSON simples, sem banco de dados e sem dependências novas."
Write-Host ""

foreach ($Path in @(
    (Join-Path $Root "runtime\python\python.exe"),
    (Join-Path $Root "app\server.py"),
    (Join-Path $Root "app\engine_manager.py"),
    (Join-Path $Root "ui\index.html"),
    (Join-Path $Root "ui\app.css"),
    (Join-Path $Root "ui\app.js"),
    (Join-Path $Root "profiles\machines"),
    $Payload
)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        Fail "Base V0.6.0 ausente ou incompleta: $Path"
    }
}

$Answer = Read-Host "Instalar a V0.6.1 agora? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) {
    Write-Host "Cancelado."
    exit 0
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root ("backup\pre_v0_6_1_" + $Stamp)
New-Item -ItemType Directory -Force -Path (Join-Path $BackupDir "app") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $BackupDir "ui") | Out-Null

Write-Host ""
Write-Host "1/4 - Backup da interface V0.6.0..."
foreach ($Rel in @(
    "VERSION.json",
    "app\server.py",
    "ui\index.html",
    "ui\app.css",
    "ui\app.js"
)) {
    $Source = Join-Path $Root $Rel
    if (Test-Path -LiteralPath $Source) {
        $Dest = Join-Path $BackupDir $Rel
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Dest) | Out-Null
        Copy-Item -LiteralPath $Source -Destination $Dest -Force
    }
}

Write-Host "2/4 - Instalando Sessões e Histórico..."
Get-ChildItem -LiteralPath $Payload -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $Root -Recurse -Force
}
New-Item -ItemType Directory -Force -Path (Join-Path $Root "sessions") | Out-Null

Write-Host "3/4 - Validando módulos Python..."
$Python = Join-Path $Root "runtime\python\python.exe"
& $Python -m py_compile `
    (Join-Path $Root "app\server.py") `
    (Join-Path $Root "app\sessions.py")
if ($LASTEXITCODE -ne 0) {
    Fail "Falha na validação Python."
}

Write-Host "4/4 - Gravando estado da instalação..."
$StateDir = Join-Path $Root "state"
New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
$State = [PSCustomObject]@{
    product = "NUCLEO IA PORTATIL"
    version = "0.6.1"
    installed_at = (Get-Date).ToString("o")
    backup_dir = $BackupDir
}
$State | ConvertTo-Json -Depth 4 |
    Set-Content (Join-Path $StateDir "v0_6_1_install.json") -Encoding UTF8

Write-Host ""
Write-Host "============================================================================"
Write-Host "V0.6.1 INSTALADA COM SUCESSO"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Agora execute normalmente:"
Write-Host "  $Root\INICIAR_NUCLEO_IA.bat"
Write-Host ""
Write-Host "As conversas serão salvas em:"
Write-Host "  $Root\sessions"
