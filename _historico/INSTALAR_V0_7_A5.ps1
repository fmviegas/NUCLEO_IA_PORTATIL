# NUCLEO IA PORTATIL - V0.7 Fase 3 fatia 3 (alpha5) - motor resolve modelo por id
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Payload = Join-Path $Root "payload"

function Fail([string]$Message) {
    Write-Host ""; Write-Host "ERRO: $Message" -ForegroundColor Red; Write-Host ""; exit 1
}

Write-Host ""
Write-Host "============================================================================"
Write-Host "        NUCLEO IA PORTATIL - V0.7 FASE 3 fatia 3 (alpha5)"
Write-Host "        Motor resolve o modelo por id (catalogo em runtime)"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Alpha. Base de retorno: V0.6.5 FINAL." -ForegroundColor Yellow
Write-Host ""

foreach ($Path in @(
    (Join-Path $Root "runtime\python\python.exe"),
    (Join-Path $Root "app\engine_manager.py"),
    (Join-Path $Root "app\catalog.py"),
    $Payload,
    (Join-Path $Payload "app\engine_manager.py"),
    (Join-Path $Payload "VERSION.json")
)) {
    if (-not (Test-Path -LiteralPath $Path)) { Fail "Base ausente/incompleta: $Path" }
}

$Answer = Read-Host "Instalar V0.7 Fase 3 fatia 3 (alpha5) agora? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) { Write-Host "Cancelado."; exit 0 }

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root ("backup\pre_v0_7_a5_files_" + $Stamp)
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

Write-Host ""
Write-Host "1/4 - Criando rollback tecnico..."
foreach ($Rel in @("VERSION.json", "app\engine_manager.py")) {
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
& $Python -m py_compile (Join-Path $Root "app\engine_manager.py") (Join-Path $Root "app\server.py")
if ($LASTEXITCODE -ne 0) { Fail "Falha no compile. Use ROLLBACK_V0_7_A5.bat." }

Write-Host "4/4 - Gravando estado..."
New-Item -ItemType Directory -Force -Path (Join-Path $Root "state") | Out-Null
$State = [PSCustomObject]@{
    product="NUCLEO IA PORTATIL"; version="0.7.0-alpha5"; based_on="0.7.0-alpha4"
    installed_at=(Get-Date).ToString("o"); backup_dir=$BackupDir
    purpose="phase3-slice3-engine-resolves-model-by-id"
    changed=@("VERSION.json","app/engine_manager.py")
}
$State | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $Root "state\v0_7_a5_install.json") -Encoding UTF8

Write-Host ""
Write-Host "============================================================================"
Write-Host "V0.7 FASE 3 fatia 3 (alpha5) INSTALADA"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Backup tecnico: $BackupDir"
Write-Host "Reabra o NUCLEO, alterne RAPIDO/QUALIDADE e confirme a geracao (Detalhes mostra model_id)."
Write-Host ""
