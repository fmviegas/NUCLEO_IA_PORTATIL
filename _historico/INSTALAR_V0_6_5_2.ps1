# NUCLEO IA PORTATIL - PATCH V0.6.5.2 - Leitura Semantica de Planilhas
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
Write-Host "        NUCLEO IA PORTATIL - PATCH V0.6.5.2"
Write-Host "        Leitura Semantica de Planilhas (formulario/calculadora)"
Write-Host "============================================================================"
Write-Host ""

foreach ($Path in @(
    (Join-Path $Root "runtime\python\python.exe"),
    (Join-Path $Root "app\server.py"),
    (Join-Path $Root "app\engine_manager.py"),
    (Join-Path $Root "app\workspace.py"),
    (Join-Path $Root "app\file_analysis.py"),
    $Payload,
    (Join-Path $Payload "VERSION.json")
)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        Fail "Base V0.6.5.x ausente ou incompleta: $Path"
    }
}

# VERSION.json na raiz e apenas metadado; o patch o (re)grava a partir do
# payload. Se estiver ausente na raiz (limpeza anterior), apenas avisamos.
if (-not (Test-Path -LiteralPath (Join-Path $Root "VERSION.json"))) {
    Write-Host "Aviso: VERSION.json ausente na raiz; sera criado a partir do payload." -ForegroundColor Yellow
}

$Answer = Read-Host "Instalar o patch V0.6.5.2 agora? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) {
    Write-Host "Cancelado."
    exit 0
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root ("backup\pre_v0_6_5_2_files_" + $Stamp)
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

Write-Host ""
Write-Host "1/4 - Criando rollback tecnico..."
foreach ($Rel in @(
    "VERSION.json",
    "app\workspace.py",
    "app\file_analysis.py"
)) {
    $Source = Join-Path $Root $Rel
    if (Test-Path -LiteralPath $Source) {
        $Dest = Join-Path $BackupDir $Rel
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Dest) | Out-Null
        Copy-Item -LiteralPath $Source -Destination $Dest -Force
    }
}

Write-Host "2/4 - Aplicando patch..."
Get-ChildItem -LiteralPath $Payload -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $Root -Recurse -Force
}

Write-Host "3/4 - Validando Python..."
$Python = Join-Path $Root "runtime\python\python.exe"
& $Python -m py_compile `
    (Join-Path $Root "app\server.py") `
    (Join-Path $Root "app\engine_manager.py") `
    (Join-Path $Root "app\workspace.py") `
    (Join-Path $Root "app\file_analysis.py")
if ($LASTEXITCODE -ne 0) {
    Fail "Falha na validacao Python. Use ROLLBACK_V0_6_5_2.bat se necessario."
}

Write-Host "4/4 - Gravando estado..."
$State = [PSCustomObject]@{
    product      = "NUCLEO IA PORTATIL"
    version      = "0.6.5.2"
    installed_at = (Get-Date).ToString("o")
    backup_dir   = $BackupDir
    purpose      = "semantic-spreadsheet-reading"
    changed      = @("VERSION.json","app/workspace.py","app/file_analysis.py")
}
New-Item -ItemType Directory -Force -Path (Join-Path $Root "state") | Out-Null
$State | ConvertTo-Json -Depth 4 |
    Set-Content (Join-Path $Root "state\v0_6_5_2_install.json") -Encoding UTF8

Write-Host ""
Write-Host "============================================================================"
Write-Host "PATCH V0.6.5.2 INSTALADO"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Backup tecnico: $BackupDir"
Write-Host "Reabra o NUCLEO e repita a analise da planilha de precificacao."
Write-Host ""
