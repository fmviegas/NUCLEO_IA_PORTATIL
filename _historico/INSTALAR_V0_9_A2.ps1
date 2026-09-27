# NUCLEO IA PORTATIL - V0.9 Escritor 360 (alpha2) - outline via LLM
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Payload = Join-Path $Root "payload"

function Fail([string]$Message) {
    Write-Host ""; Write-Host "ERRO: $Message" -ForegroundColor Red; Write-Host ""; exit 1
}

Write-Host ""
Write-Host "============================================================================"
Write-Host "        NUCLEO IA PORTATIL - V0.9 ESCRITOR 360 (alpha2)"
Write-Host "        Geracao de outline via LLM"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Alpha. Requer a fatia 1 (planner/personas). Base de retorno: V0.7 FINAL." -ForegroundColor Yellow
Write-Host ""

foreach ($Path in @(
    (Join-Path $Root "runtime\python\python.exe"),
    (Join-Path $Root "app\book\planner.py"),
    (Join-Path $Root "app\engine_manager.py"),
    $Payload,
    (Join-Path $Payload "app\book\outline.py"),
    (Join-Path $Payload "VERSION.json")
)) {
    if (-not (Test-Path -LiteralPath $Path)) { Fail "Base ausente/incompleta (instale a fatia 1?): $Path" }
}

$Answer = Read-Host "Instalar V0.9 Escritor 360 (alpha2) agora? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) { Write-Host "Cancelado."; exit 0 }

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root ("backup\pre_v0_9_a2_files_" + $Stamp)
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

Write-Host "1/4 - Criando rollback tecnico..."
Copy-Item -LiteralPath (Join-Path $Root "VERSION.json") -Destination (Join-Path $BackupDir "VERSION.json") -Force

Write-Host "2/4 - Aplicando patch..."
Get-ChildItem -LiteralPath $Payload -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $Root -Recurse -Force
}
$py = "runtime\python\python.exe"
Set-Content (Join-Path $Root "OUTLINE.bat") "@echo off`r`nsetlocal`r`ncd /d `"%~dp0`"`r`nchcp 65001 >nul`r`nset PYTHONUTF8=1`r`n`"$py`" `"app\book\outline.py`" %*`r`npause`r`n" -Encoding ascii

Write-Host "3/4 - Validando Python..."
$Python = Join-Path $Root "runtime\python\python.exe"
& $Python -m py_compile (Join-Path $Root "app\book\outline.py")
if ($LASTEXITCODE -ne 0) { Fail "Falha no compile. Use ROLLBACK_V0_9_A2.bat." }

Write-Host "4/4 - Gravando estado..."
New-Item -ItemType Directory -Force -Path (Join-Path $Root "state") | Out-Null
$State = [PSCustomObject]@{
    product="NUCLEO IA PORTATIL"; version="0.9.0-alpha2"; based_on="0.9.0-alpha1"
    installed_at=(Get-Date).ToString("o"); backup_dir=$BackupDir
    purpose="book-writer-360-slice2-outline-llm"
    added=@("app/book/outline.py","OUTLINE.bat"); changed=@("VERSION.json")
}
$State | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $Root "state\v0_9_a2_install.json") -Encoding UTF8

Write-Host ""
Write-Host "V0.9 ESCRITOR 360 (alpha2) INSTALADA"
Write-Host ""
Write-Host "Gerar outline:  OUTLINE.bat gerar --dir workspace\livros\<slug>"
Write-Host "Aplicar titulos: OUTLINE.bat aplicar --dir workspace\livros\<slug>"
Write-Host ""
