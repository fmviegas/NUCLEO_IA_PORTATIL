# NUCLEO IA PORTATIL - V0.9 Escritor 360 (alpha1) - scaffolder + planner + linter
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Payload = Join-Path $Root "payload"

function Fail([string]$Message) {
    Write-Host ""; Write-Host "ERRO: $Message" -ForegroundColor Red; Write-Host ""; exit 1
}

Write-Host ""
Write-Host "============================================================================"
Write-Host "        NUCLEO IA PORTATIL - V0.9 ESCRITOR 360 (alpha1)"
Write-Host "        Scaffolder de livros + planner + linter anti-IA"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Alpha. Offline; nao altera o motor. Base de retorno: V0.7 FINAL." -ForegroundColor Yellow
Write-Host ""

foreach ($Path in @(
    (Join-Path $Root "runtime\python\python.exe"),
    $Payload,
    (Join-Path $Payload "app\book\book_project.py"),
    (Join-Path $Payload "app\book\planner.py"),
    (Join-Path $Payload "app\book\humanizar.py"),
    (Join-Path $Payload "config\personas\ficcao_360.md"),
    (Join-Path $Payload "config\personas\tecnico_360.md"),
    (Join-Path $Payload "config\personas\humanizacao.md"),
    (Join-Path $Payload "VERSION.json")
)) {
    if (-not (Test-Path -LiteralPath $Path)) { Fail "Base ausente/incompleta: $Path" }
}

$Answer = Read-Host "Instalar V0.9 Escritor 360 (alpha1) agora? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) { Write-Host "Cancelado."; exit 0 }

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root ("backup\pre_v0_9_a1_files_" + $Stamp)
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

Write-Host ""
Write-Host "1/4 - Criando rollback tecnico..."
Copy-Item -LiteralPath (Join-Path $Root "VERSION.json") -Destination (Join-Path $BackupDir "VERSION.json") -Force

Write-Host "2/4 - Aplicando patch..."
Get-ChildItem -LiteralPath $Payload -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $Root -Recurse -Force
}
# Lancadores de conveniencia (UTF-8) na raiz
$py = "runtime\python\python.exe"
Set-Content (Join-Path $Root "CRIAR_LIVRO.bat") "@echo off`r`nsetlocal`r`ncd /d `"%~dp0`"`r`nchcp 65001 >nul`r`nset PYTHONUTF8=1`r`n`"$py`" `"app\book\book_project.py`" criar %*`r`npause`r`n" -Encoding ascii
Set-Content (Join-Path $Root "PLANO_LIVRO.bat") "@echo off`r`nsetlocal`r`ncd /d `"%~dp0`"`r`nchcp 65001 >nul`r`nset PYTHONUTF8=1`r`n`"$py`" `"app\book\planner.py`" %*`r`npause`r`n" -Encoding ascii
Set-Content (Join-Path $Root "HUMANIZAR.bat") "@echo off`r`nsetlocal`r`ncd /d `"%~dp0`"`r`nchcp 65001 >nul`r`nset PYTHONUTF8=1`r`n`"$py`" `"app\book\humanizar.py`" %*`r`npause`r`n" -Encoding ascii

Write-Host "3/4 - Validando Python..."
$Python = Join-Path $Root "runtime\python\python.exe"
& $Python -m py_compile `
    (Join-Path $Root "app\book\book_project.py") `
    (Join-Path $Root "app\book\planner.py") `
    (Join-Path $Root "app\book\humanizar.py")
if ($LASTEXITCODE -ne 0) { Fail "Falha no compile. Use ROLLBACK_V0_9_A1.bat." }
& $Python (Join-Path $Root "app\book\planner.py") generos | Out-Null
if ($LASTEXITCODE -ne 0) { Fail "planner nao rodou. Use ROLLBACK_V0_9_A1.bat." }

Write-Host "4/4 - Gravando estado..."
New-Item -ItemType Directory -Force -Path (Join-Path $Root "state") | Out-Null
$State = [PSCustomObject]@{
    product="NUCLEO IA PORTATIL"; version="0.9.0-alpha1"; based_on="0.7-final"
    installed_at=(Get-Date).ToString("o"); backup_dir=$BackupDir
    purpose="book-writer-360-slice1-scaffolder-planner-linter"
    added=@("app/book/","config/personas/","CRIAR_LIVRO.bat","PLANO_LIVRO.bat","HUMANIZAR.bat")
    changed=@("VERSION.json")
}
$State | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $Root "state\v0_9_a1_install.json") -Encoding UTF8

Write-Host ""
Write-Host "============================================================================"
Write-Host "V0.9 ESCRITOR 360 (alpha1) INSTALADA"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Crie um livro:  CRIAR_LIVRO.bat --slug meu-livro --genero romance_padrao --titulo \"T\" --autor \"A\""
Write-Host "Generos:        PLANO_LIVRO.bat generos"
Write-Host "Linter anti-IA: HUMANIZAR.bat workspace\livros\meu-livro\04_CAPITULOS"
Write-Host ""
