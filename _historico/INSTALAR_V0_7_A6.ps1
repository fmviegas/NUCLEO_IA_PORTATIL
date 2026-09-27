# NUCLEO IA PORTATIL - V0.7 Fase 3 fatia 4 (alpha6) - validar_modelo.py (§25)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Payload = Join-Path $Root "payload"

function Fail([string]$Message) {
    Write-Host ""; Write-Host "ERRO: $Message" -ForegroundColor Red; Write-Host ""; exit 1
}

Write-Host ""
Write-Host "============================================================================"
Write-Host "        NUCLEO IA PORTATIL - V0.7 FASE 3 fatia 4 (alpha6)"
Write-Host "        validar_modelo.py - portao de validacao de modelo (sec.25)"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Alpha. Arquivo novo; nao altera o motor. Base de retorno: V0.6.5 FINAL." -ForegroundColor Yellow
Write-Host ""

foreach ($Path in @(
    (Join-Path $Root "runtime\python\python.exe"),
    $Payload,
    (Join-Path $Payload "tools\validar_modelo.py"),
    (Join-Path $Payload "VERSION.json")
)) {
    if (-not (Test-Path -LiteralPath $Path)) { Fail "Base ausente/incompleta: $Path" }
}

$Answer = Read-Host "Instalar V0.7 Fase 3 fatia 4 (alpha6) agora? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) { Write-Host "Cancelado."; exit 0 }

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root ("backup\pre_v0_7_a6_files_" + $Stamp)
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

Write-Host ""
Write-Host "1/4 - Criando rollback tecnico..."
foreach ($Rel in @("VERSION.json", "tools\validar_modelo.py")) {
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

Write-Host "3/4 - Validando (compile + autoteste com modelos presentes)..."
$Python = Join-Path $Root "runtime\python\python.exe"
& $Python -m py_compile (Join-Path $Root "tools\validar_modelo.py")
if ($LASTEXITCODE -ne 0) { Fail "Falha no compile. Use ROLLBACK_V0_7_A6.bat." }
& $Python (Join-Path $Root "tools\validar_modelo.py") --id qwen3-4b-q4km | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Host "Aviso: autoteste do 4B retornou falha/aviso; revise a saida acima." -ForegroundColor Yellow
}

Write-Host "4/4 - Gravando estado..."
New-Item -ItemType Directory -Force -Path (Join-Path $Root "state") | Out-Null
$State = [PSCustomObject]@{
    product="NUCLEO IA PORTATIL"; version="0.7.0-alpha6"; based_on="0.7.0-alpha5"
    installed_at=(Get-Date).ToString("o"); backup_dir=$BackupDir
    purpose="phase3-slice4-model-validation-gate"
    changed=@("VERSION.json"); added=@("tools/validar_modelo.py")
}
$State | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $Root "state\v0_7_a6_install.json") -Encoding UTF8

Write-Host ""
Write-Host "============================================================================"
Write-Host "V0.7 FASE 3 fatia 4 (alpha6) INSTALADA"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Uso: runtime\python\python.exe tools\validar_modelo.py <arquivo.gguf> [--sha256 HEX]"
Write-Host "     runtime\python\python.exe tools\validar_modelo.py --id <model_id>"
Write-Host ""
