# NUCLEO IA PORTATIL - CONSOLIDACAO V0.7 FINAL (Portabilidade Real)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Payload = Join-Path $Root "payload"

function Fail([string]$Message) {
    Write-Host ""; Write-Host "ERRO: $Message" -ForegroundColor Red; Write-Host ""; exit 1
}

Write-Host ""
Write-Host "============================================================================"
Write-Host "        NUCLEO IA PORTATIL - CONSOLIDACAO V0.7 FINAL"
Write-Host "        Portabilidade Real (deteccao, fallback CPU, catalogo de modelos)"
Write-Host "============================================================================"
Write-Host ""

foreach ($Path in @(
    (Join-Path $Root "runtime\python\python.exe"),
    (Join-Path $Root "app\engine_manager.py"),
    (Join-Path $Root "app\catalog.py"),
    (Join-Path $Root "app\autotune.py"),
    (Join-Path $Root "config\models_registry.json"),
    (Join-Path $Root "tools\validar_modelo.py"),
    $Payload,
    (Join-Path $Payload "VERSION.json"),
    (Join-Path $Payload "tools\validar_v0_7_final.py"),
    (Join-Path $Payload "app\manifests\manifest_v0_7_final.json")
)) {
    if (-not (Test-Path -LiteralPath $Path)) { Fail "Base V0.7 ausente/incompleta: $Path" }
}

foreach ($st in @("v0_7_a1_install.json","v0_7_a2_install.json","v0_7_a3_install.json",
                  "v0_7_a4_install.json","v0_7_a5_install.json","v0_7_a6_install.json")) {
    if (-not (Test-Path -LiteralPath (Join-Path $Root ("state\" + $st)))) {
        Write-Host "Aviso: state\$st ausente. Instale todos os alphas 1-6 antes de consolidar." -ForegroundColor Yellow
    }
}

$Answer = Read-Host "Consolidar a V0.7 FINAL agora? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) { Write-Host "Cancelado."; exit 0 }

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root ("backup\pre_v0_7_final_" + $Stamp)
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

Write-Host ""
Write-Host "1/4 - Criando rollback tecnico..."
foreach ($Rel in @("VERSION.json",
                   "app\manifests\manifest_v0_7_final.json",
                   "tools\validar_v0_7_final.py",
                   "docs\RELEASE_V0_7_FINAL.md")) {
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

Write-Host "3/4 - Validando V0.7 FINAL..."
$Python = Join-Path $Root "runtime\python\python.exe"
& $Python (Join-Path $Root "tools\validar_v0_7_final.py")
if ($LASTEXITCODE -ne 0) { Fail "Validacao falhou. Use ROLLBACK_V0_7_FINAL.bat se necessario." }

Write-Host "4/4 - Gravando estado de consolidacao..."
New-Item -ItemType Directory -Force -Path (Join-Path $Root "state") | Out-Null
$State = [PSCustomObject]@{
    product="NUCLEO IA PORTATIL"; version="0.7"; edition="FINAL"; channel="stable"
    consolidated_from=@("0.6-final","0.6.5-final","0.7.0-alpha1","0.7.0-alpha2",
                        "0.7.0-alpha3","0.7.0-alpha4","0.7.0-alpha5","0.7.0-alpha6")
    consolidated_at=(Get-Date).ToString("o"); backup_dir=$BackupDir
}
$State | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $Root "state\v0_7_final_install.json") -Encoding UTF8

Write-Host ""
Write-Host "============================================================================"
Write-Host "V0.7 FINAL CONSOLIDADA"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Base estavel de retorno (junto com V0.6 FINAL e V0.6.5 FINAL)."
Write-Host "Backup tecnico: $BackupDir"
Write-Host "Reconferir a qualquer momento: VALIDAR_V0_7_FINAL.bat"
Write-Host ""
