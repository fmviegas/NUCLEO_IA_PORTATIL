# NUCLEO IA PORTATIL - V0.9 Escritor 360 (alpha3) - outline em lotes (anti-loop)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Payload = Join-Path $Root "payload"

function Fail([string]$Message) {
    Write-Host ""; Write-Host "ERRO: $Message" -ForegroundColor Red; Write-Host ""; exit 1
}

Write-Host ""
Write-Host "        NUCLEO IA PORTATIL - V0.9 ESCRITOR 360 (alpha3) - outline em lotes"
Write-Host ""
Write-Host "Alpha. Requer fatias 1 e 2. Base de retorno: V0.7 FINAL." -ForegroundColor Yellow

foreach ($Path in @(
    (Join-Path $Root "runtime\python\python.exe"),
    (Join-Path $Root "app\book\outline.py"),
    $Payload,
    (Join-Path $Payload "app\book\outline.py"),
    (Join-Path $Payload "VERSION.json")
)) {
    if (-not (Test-Path -LiteralPath $Path)) { Fail "Base ausente/incompleta (instale as fatias 1 e 2?): $Path" }
}

$Answer = Read-Host "Instalar V0.9 (alpha3) agora? [S/n]"
if ($Answer -and $Answer.ToLowerInvariant() -notin @("s","sim","y","yes")) { Write-Host "Cancelado."; exit 0 }

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root ("backup\pre_v0_9_a3_files_" + $Stamp)
New-Item -ItemType Directory -Force -Path (Join-Path $BackupDir "app\book") | Out-Null
Copy-Item -LiteralPath (Join-Path $Root "VERSION.json") -Destination (Join-Path $BackupDir "VERSION.json") -Force
Copy-Item -LiteralPath (Join-Path $Root "app\book\outline.py") -Destination (Join-Path $BackupDir "app\book\outline.py") -Force

Write-Host "Aplicando patch..."
Get-ChildItem -LiteralPath $Payload -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $Root -Recurse -Force
}

Write-Host "Validando Python..."
$Python = Join-Path $Root "runtime\python\python.exe"
& $Python -m py_compile (Join-Path $Root "app\book\outline.py")
if ($LASTEXITCODE -ne 0) { Fail "Falha no compile. Use ROLLBACK_V0_9_A3.bat." }

New-Item -ItemType Directory -Force -Path (Join-Path $Root "state") | Out-Null
$State = [PSCustomObject]@{
    product="NUCLEO IA PORTATIL"; version="0.9.0-alpha3"; based_on="0.9.0-alpha2"
    installed_at=(Get-Date).ToString("o"); backup_dir=$BackupDir
    purpose="book-writer-360-slice2.1-outline-batched-anti-loop"
    changed=@("VERSION.json","app/book/outline.py")
}
$State | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $Root "state\v0_9_a3_install.json") -Encoding UTF8

Write-Host ""
Write-Host "V0.9 (alpha3) INSTALADA. Rode:"
Write-Host "  OUTLINE.bat gerar --dir workspace\livros\<slug> --modo quality"
Write-Host ""
