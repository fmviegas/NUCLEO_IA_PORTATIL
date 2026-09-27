$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
function Fail($m){ Write-Host ""; Write-Host "ERRO: $m" -ForegroundColor Red; exit 1 }
$Latest = Get-ChildItem (Join-Path $Root "backup") -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "pre_v0_9_a4_files_*" } | Sort-Object Name -Descending | Select-Object -First 1
if(-not $Latest){ Fail "backup pre_v0_9_a4_files_* nao encontrado" }
$a = Read-Host "Reverter alpha4 (voltar ao alpha3)? [S/n]"; if($a -and $a.ToLowerInvariant() -notin @("s","sim","y","yes")){ Write-Host "Cancelado."; exit 0 }
foreach($Rel in @("VERSION.json","app\book\outline.py")){ $src=Join-Path $Latest.FullName $Rel; if(Test-Path -LiteralPath $src){ Copy-Item $src (Join-Path $Root $Rel) -Force; $pl=Join-Path (Join-Path $Root "payload") $Rel; if(Test-Path -LiteralPath (Split-Path -Parent $pl)){ Copy-Item $src $pl -Force }; Write-Host "restaurado: $Rel" } }
$s=Join-Path $Root "state\v0_9_a4_install.json"; if(Test-Path -LiteralPath $s){ Remove-Item -LiteralPath $s -Force }
Write-Host ""; Write-Host "ROLLBACK CONCLUIDO. Estado: V0.9.0-alpha3."; Write-Host ""
