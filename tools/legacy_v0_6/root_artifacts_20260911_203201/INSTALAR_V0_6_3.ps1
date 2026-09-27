# NUCLEO IA PORTATIL - INSTALADOR V0.6.3
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
Write-Host "             NUCLEO IA PORTATIL - V0.6.3"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Manutencao e Recuperacao pela Interface"
Write-Host "Reparo local: nenhum download, nenhum modelo alterado."
Write-Host ""

foreach ($Path in @(
    (Join-Path $Root "runtime\python\python.exe"),
    (Join-Path $Root "app\server.py"),
    (Join-Path $Root "app\engine_manager.py"),
    (Join-Path $Root "app\calibration_manager.py"),
    (Join-Path $Root "app\autotune.py"),
    (Join-Path $Root "app\sessions.py"),
    (Join-Path $Root "ui\index.html"),
    (Join-Path $Root "cache\downloads"),
    $Payload
)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        Fail "Base V0.6.2.x ausente ou incompleta: $Path"
    }
}

$VersionPath = Join-Path $Root "VERSION.json"
if (Test-Path -LiteralPath $VersionPath) {
    try {
        $Current = Get-Content -LiteralPath $VersionPath -Raw -Encoding UTF8 | ConvertFrom-Json
        Write-Host ("Versao atual detectada: {0}" -f $Current.version)
    }
    catch {
        Write-Host "Aviso: nao foi possivel ler VERSION.json atual." -ForegroundColor Yellow
    }
}

$Answer = Read-Host "Instalar a V0.6.3 agora? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) {
    Write-Host "Cancelado."
    exit 0
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root ("backup\pre_v0_6_3_" + $Stamp)

foreach ($Dir in @("app","ui","config")) {
    New-Item -ItemType Directory -Force -Path (Join-Path $BackupDir $Dir) | Out-Null
}

Write-Host ""
Write-Host "1/4 - Backup da interface atual..."
foreach ($Rel in @(
    "VERSION.json",
    "app\server.py",
    "app\engine_manager.py",
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

Write-Host "2/4 - Instalando Manutencao e Recuperacao..."
Get-ChildItem -LiteralPath $Payload -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $Root -Recurse -Force
}

Write-Host "3/4 - Validando modulos Python..."
$Python = Join-Path $Root "runtime\python\python.exe"
& $Python -m py_compile `
    (Join-Path $Root "app\server.py") `
    (Join-Path $Root "app\engine_manager.py") `
    (Join-Path $Root "app\maintenance_manager.py")
if ($LASTEXITCODE -ne 0) {
    Fail "Falha na validacao Python."
}

Write-Host "4/4 - Gravando estado da instalacao..."
$StateDir = Join-Path $Root "state"
New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
$State = [PSCustomObject]@{
    product = "NUCLEO IA PORTATIL"
    version = "0.6.3"
    installed_at = (Get-Date).ToString("o")
    backup_dir = $BackupDir
}
$State | ConvertTo-Json -Depth 4 |
    Set-Content (Join-Path $StateDir "v0_6_3_install.json") -Encoding UTF8

Write-Host ""
Write-Host "============================================================================"
Write-Host "V0.6.3 INSTALADA COM SUCESSO"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Abra normalmente:"
Write-Host "  $Root\INICIAR_NUCLEO_IA.bat"
Write-Host ""
Write-Host "Na interface, clique em Manutencao."
