# NUCLEO IA PORTATIL - CONSOLIDACAO V0.6.5 FINAL
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
Write-Host "        NUCLEO IA PORTATIL - CONSOLIDACAO V0.6.5 FINAL"
Write-Host "        Analise Local com leitura semantica de planilhas"
Write-Host "============================================================================"
Write-Host ""

# Pre-requisitos: base 0.6.5.x aplicada.
foreach ($Path in @(
    (Join-Path $Root "runtime\python\python.exe"),
    (Join-Path $Root "app\server.py"),
    (Join-Path $Root "app\engine_manager.py"),
    (Join-Path $Root "app\file_analysis.py"),
    (Join-Path $Root "app\workspace.py"),
    $Payload,
    (Join-Path $Payload "VERSION.json"),
    (Join-Path $Payload "tools\validar_v0_6_5_final.py"),
    (Join-Path $Payload "app\manifests\manifest_v0_6_5_final.json")
)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        Fail "Base 0.6.5.x ausente ou incompleta: $Path"
    }
}

# Aviso se a linha 0.6.5.x nao estiver toda instalada.
foreach ($st in @("v0_6_5_2_install.json","v0_6_5_3_install.json","v0_6_5_4_install.json")) {
    if (-not (Test-Path -LiteralPath (Join-Path $Root ("state\" + $st)))) {
        Write-Host "Aviso: state\$st ausente. Instale a linha 0.6.5.x antes de consolidar." -ForegroundColor Yellow
    }
}

$Answer = Read-Host "Consolidar a V0.6.5 FINAL agora? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) {
    Write-Host "Cancelado."
    exit 0
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root ("backup\pre_v0_6_5_final_" + $Stamp)
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

Write-Host ""
Write-Host "1/4 - Criando rollback tecnico..."
foreach ($Rel in @(
    "VERSION.json",
    "app\manifests\manifest_v0_6_5_final.json",
    "tools\validar_v0_6_5_final.py",
    "docs\RELEASE_V0_6_5_FINAL.md"
)) {
    $Source = Join-Path $Root $Rel
    if (Test-Path -LiteralPath $Source) {
        $Dest = Join-Path $BackupDir $Rel
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Dest) | Out-Null
        Copy-Item -LiteralPath $Source -Destination $Dest -Force
    }
}

Write-Host "2/4 - Aplicando consolidacao (VERSION/manifest/validador/release)..."
Get-ChildItem -LiteralPath $Payload -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $Root -Recurse -Force
}

Write-Host "3/4 - Validando V0.6.5 FINAL..."
$Python = Join-Path $Root "runtime\python\python.exe"
& $Python (Join-Path $Root "tools\validar_v0_6_5_final.py")
if ($LASTEXITCODE -ne 0) {
    Fail "Validacao falhou. Use ROLLBACK_V0_6_5_FINAL.bat se necessario."
}

Write-Host "4/4 - Gravando estado de consolidacao..."
New-Item -ItemType Directory -Force -Path (Join-Path $Root "state") | Out-Null
$State = [PSCustomObject]@{
    product        = "NUCLEO IA PORTATIL"
    version        = "0.6.5"
    edition        = "FINAL"
    channel        = "stable"
    consolidated_from = @("0.6-final","0.6.5","0.6.5.1","0.6.5.2","0.6.5.3","0.6.5.4")
    consolidated_at = (Get-Date).ToString("o")
    backup_dir     = $BackupDir
}
$State | ConvertTo-Json -Depth 5 |
    Set-Content (Join-Path $Root "state\v0_6_5_final_install.json") -Encoding UTF8

Write-Host ""
Write-Host "============================================================================"
Write-Host "V0.6.5 FINAL CONSOLIDADA"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Base estavel de retorno (junto com a V0.6 FINAL)."
Write-Host "Backup tecnico: $BackupDir"
Write-Host "Rode VALIDAR_V0_6_5_FINAL.bat quando quiser reconferir a integridade."
Write-Host ""
