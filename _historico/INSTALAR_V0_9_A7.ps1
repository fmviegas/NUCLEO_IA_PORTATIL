$ErrorActionPreference="Stop"; $Root=Split-Path -Parent $MyInvocation.MyCommand.Path; $Payload=Join-Path $Root "payload"
function Fail($m){Write-Host "";Write-Host "ERRO: $m" -ForegroundColor Red;exit 1}
Write-Host ""; Write-Host "  NUCLEO IA - V0.9 (alpha7) - revisao e compilacao"; Write-Host ""
foreach($p in @((Join-Path $Root "runtime\python\python.exe"),(Join-Path $Root "app\book\humanizar.py"),$Payload,(Join-Path $Payload "app\book\revisar.py"),(Join-Path $Payload "VERSION.json"))){if(-not(Test-Path -LiteralPath $p)){Fail "ausente (instale fatia 1?): $p"}}
$a=Read-Host "Instalar V0.9 (alpha7)? [S/n]"; if($a -and $a.ToLowerInvariant() -notin @("s","sim","y","yes")){Write-Host "Cancelado.";exit 0}
$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"; $BackupDir=Join-Path $Root ("backup\pre_v0_9_a7_files_"+$Stamp)
New-Item -ItemType Directory -Force -Path $BackupDir|Out-Null
Copy-Item (Join-Path $Root "VERSION.json") (Join-Path $BackupDir "VERSION.json") -Force
Get-ChildItem -LiteralPath $Payload -Force|ForEach-Object{Copy-Item -LiteralPath $_.FullName -Destination $Root -Recurse -Force}
$py="runtime\python\python.exe"
Set-Content (Join-Path $Root "REVISAR.bat") "@echo off`r`nsetlocal`r`ncd /d `"%~dp0`"`r`nchcp 65001 >nul`r`nset PYTHONUTF8=1`r`n`"$py`" `"app\book\revisar.py`" %*`r`npause`r`n" -Encoding ascii
$Python=Join-Path $Root "runtime\python\python.exe"; & $Python -m py_compile (Join-Path $Root "app\book\revisar.py"); if($LASTEXITCODE -ne 0){Fail "compile falhou (use ROLLBACK_V0_9_A7.bat)"}
New-Item -ItemType Directory -Force -Path (Join-Path $Root "state")|Out-Null
[PSCustomObject]@{product="NUCLEO IA PORTATIL";version="0.9.0-alpha7";based_on="0.9.0-alpha6";installed_at=(Get-Date).ToString("o");backup_dir=$BackupDir;added=@("app/book/revisar.py","REVISAR.bat");changed=@("VERSION.json")}|ConvertTo-Json -Depth 4|Set-Content (Join-Path $Root "state\v0_9_a7_install.json") -Encoding UTF8
Write-Host ""; Write-Host "V0.9 (alpha7) INSTALADA. Rode: REVISAR.bat tudo --dir workspace\livros\<slug>"; Write-Host ""
