# NUCLEO IA PORTATIL - HOTFIX V0.6.5.3 - Reaper de engines orfas (anti-401)
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
Write-Host "        NUCLEO IA PORTATIL - HOTFIX V0.6.5.3"
Write-Host "        Reaper de engines orfas (corrige HTTP 401 Invalid API Key)"
Write-Host "============================================================================"
Write-Host ""

foreach ($Path in @(
    (Join-Path $Root "runtime\python\python.exe"),
    (Join-Path $Root "app\server.py"),
    (Join-Path $Root "app\engine_manager.py"),
    $Payload,
    (Join-Path $Payload "app\engine_manager.py"),
    (Join-Path $Payload "VERSION.json")
)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        Fail "Base ausente ou incompleta: $Path"
    }
}

if (-not (Test-Path -LiteralPath (Join-Path $Root "VERSION.json"))) {
    Write-Host "Aviso: VERSION.json ausente na raiz; sera criado a partir do payload." -ForegroundColor Yellow
}

$Answer = Read-Host "Instalar o hotfix V0.6.5.3 agora? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) {
    Write-Host "Cancelado."
    exit 0
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root ("backup\pre_v0_6_5_3_files_" + $Stamp)
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

Write-Host ""
Write-Host "1/4 - Criando rollback tecnico..."
foreach ($Rel in @(
    "VERSION.json",
    "app\engine_manager.py"
)) {
    $Source = Join-Path $Root $Rel
    if (Test-Path -LiteralPath $Source) {
        $Dest = Join-Path $BackupDir $Rel
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Dest) | Out-Null
        Copy-Item -LiteralPath $Source -Destination $Dest -Force
    }
}

Write-Host "2/4 - Aplicando hotfix..."
Get-ChildItem -LiteralPath $Payload -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $Root -Recurse -Force
}

Write-Host "3/4 - Validando Python..."
$Python = Join-Path $Root "runtime\python\python.exe"
& $Python -m py_compile `
    (Join-Path $Root "app\server.py") `
    (Join-Path $Root "app\engine_manager.py")
if ($LASTEXITCODE -ne 0) {
    Fail "Falha na validacao Python. Use ROLLBACK_V0_6_5_3.bat se necessario."
}

Write-Host "4/4 - Gravando estado..."
$State = [PSCustomObject]@{
    product      = "NUCLEO IA PORTATIL"
    version      = "0.6.5.3"
    installed_at = (Get-Date).ToString("o")
    backup_dir   = $BackupDir
    purpose      = "orphan-llama-server-reaping"
    changed      = @("VERSION.json","app/engine_manager.py")
}
New-Item -ItemType Directory -Force -Path (Join-Path $Root "state") | Out-Null
$State | ConvertTo-Json -Depth 4 |
    Set-Content (Join-Path $Root "state\v0_6_5_3_install.json") -Encoding UTF8

Write-Host ""
Write-Host "============================================================================"
Write-Host "HOTFIX V0.6.5.3 INSTALADO"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Backup tecnico: $BackupDir"
Write-Host "Reabra o NUCLEO. Engines orfas serao encerradas automaticamente."
Write-Host ""
