$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Payload = Join-Path $Root "payload"
function Fail($m){ Write-Host ""; Write-Host "ERRO: $m" -ForegroundColor Red; exit 1 }
Write-Host ""; Write-Host "  NUCLEO IA - V0.9 (alpha5) - escrita capitulo a capitulo"; Write-Host ""
foreach($p in @((Join-Path $Root "runtime\python\python.exe"),(Join-Path $Root "app\book\outline.py"),(Join-Path $Root "app\engine_manager.py"),$Payload,(Join-Path $Payload "app\book\escrever.py"),(Join-Path $Payload "VERSION.json"))){ if(-not(Test-Path -LiteralPath $p)){ Fail "ausente (instale fatias 1-2 antes?): $p" } }
$a = Read-Host "Instalar V0.9 (alpha5)? [S/n]"; if($a -and $a.ToLowerInvariant() -notin @("s","sim","y","yes")){ Write-Host "Cancelado."; exit 0 }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"; $BackupDir = Join-Path $Root ("backup\pre_v0_9_a5_files_"+$Stamp)
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
Copy-Item (Join-Path $Root "VERSION.json") (Join-Path $BackupDir "VERSION.json") -Force
Get-ChildItem -LiteralPath $Payload -Force | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $Root -Recurse -Force }
$py="runtime\python\python.exe"
Set-Content (Join-Path $Root "ESCREVER.bat") "@echo off`r`nsetlocal`r`ncd /d `"%~dp0`"`r`nchcp 65001 >nul`r`nset PYTHONUTF8=1`r`n`"$py`" `"app\book\escrever.py`" %*`r`npause`r`n" -Encoding ascii
$Python = Join-Path $Root "runtime\python\python.exe"
& $Python -m py_compile (Join-Path $Root "app\book\escrever.py"); if($LASTEXITCODE -ne 0){ Fail "compile falhou (use ROLLBACK_V0_9_A5.bat)" }
New-Item -ItemType Directory -Force -Path (Join-Path $Root "state") | Out-Null
[PSCustomObject]@{product="NUCLEO IA PORTATIL";version="0.9.0-alpha5";based_on="0.9.0-alpha4";installed_at=(Get-Date).ToString("o");backup_dir=$BackupDir;added=@("app/book/escrever.py","ESCREVER.bat");changed=@("VERSION.json")} | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $Root "state\v0_9_a5_install.json") -Encoding UTF8
Write-Host ""; Write-Host "V0.9 (alpha5) INSTALADA. Rode: ESCREVER.bat proximo --dir workspace\livros\<slug> --modo quality"; Write-Host ""
