$ErrorActionPreference="Stop"; $Root=Split-Path -Parent $MyInvocation.MyCommand.Path; $Payload=Join-Path $Root "payload"
function Fail($m){Write-Host "";Write-Host "ERRO: $m" -ForegroundColor Red;exit 1}
Write-Host ""; Write-Host "  NUCLEO IA - V0.9 (alpha6) - anti-repeticao na escrita"; Write-Host ""
foreach($p in @((Join-Path $Root "runtime\python\python.exe"),(Join-Path $Root "app\book\escrever.py"),$Payload,(Join-Path $Payload "app\book\escrever.py"),(Join-Path $Payload "VERSION.json"))){if(-not(Test-Path -LiteralPath $p)){Fail "ausente: $p"}}
$a=Read-Host "Instalar V0.9 (alpha6)? [S/n]"; if($a -and $a.ToLowerInvariant() -notin @("s","sim","y","yes")){Write-Host "Cancelado.";exit 0}
$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"; $BackupDir=Join-Path $Root ("backup\pre_v0_9_a6_files_"+$Stamp)
New-Item -ItemType Directory -Force -Path (Join-Path $BackupDir "app\book")|Out-Null
Copy-Item (Join-Path $Root "VERSION.json") (Join-Path $BackupDir "VERSION.json") -Force
Copy-Item (Join-Path $Root "app\book\escrever.py") (Join-Path $BackupDir "app\book\escrever.py") -Force
Get-ChildItem -LiteralPath $Payload -Force|ForEach-Object{Copy-Item -LiteralPath $_.FullName -Destination $Root -Recurse -Force}
$Python=Join-Path $Root "runtime\python\python.exe"; & $Python -m py_compile (Join-Path $Root "app\book\escrever.py"); if($LASTEXITCODE -ne 0){Fail "compile falhou"}
New-Item -ItemType Directory -Force -Path (Join-Path $Root "state")|Out-Null
[PSCustomObject]@{product="NUCLEO IA PORTATIL";version="0.9.0-alpha6";based_on="0.9.0-alpha5";installed_at=(Get-Date).ToString("o");backup_dir=$BackupDir;changed=@("VERSION.json","app/book/escrever.py")}|ConvertTo-Json -Depth 4|Set-Content (Join-Path $Root "state\v0_9_a6_install.json") -Encoding UTF8
Write-Host ""; Write-Host "V0.9 (alpha6) INSTALADA. Reescreva o cap: ESCREVER.bat capitulo --dir workspace\livros\<slug> --n 1 --modo quality"; Write-Host ""
