$ErrorActionPreference="Stop"; $Root=Split-Path -Parent $MyInvocation.MyCommand.Path
function Fail($m){Write-Host "";Write-Host "ERRO: $m" -ForegroundColor Red;exit 1}
$Latest=Get-ChildItem (Join-Path $Root "backup") -Directory -ErrorAction SilentlyContinue|Where-Object{$_.Name -like "pre_v0_9_a7_files_*"}|Sort-Object Name -Descending|Select-Object -First 1
if(-not $Latest){Fail "backup pre_v0_9_a7_files_* nao encontrado"}
$a=Read-Host "Reverter alpha7 (voltar ao alpha6)? [S/n]"; if($a -and $a.ToLowerInvariant() -notin @("s","sim","y","yes")){Write-Host "Cancelado.";exit 0}
$src=Join-Path $Latest.FullName "VERSION.json"; if(Test-Path -LiteralPath $src){Copy-Item $src (Join-Path $Root "VERSION.json") -Force; $pl=Join-Path $Root "payload\VERSION.json"; if(Test-Path -LiteralPath (Split-Path -Parent $pl)){Copy-Item $src $pl -Force}; Write-Host "restaurado: VERSION.json"}
foreach($Rel in @("app\book\revisar.py","payload\app\book\revisar.py","REVISAR.bat")){$p=Join-Path $Root $Rel; if(Test-Path -LiteralPath $p){Remove-Item -LiteralPath $p -Force; Write-Host "removido: $Rel"}}
$s=Join-Path $Root "state\v0_9_a7_install.json"; if(Test-Path -LiteralPath $s){Remove-Item -LiteralPath $s -Force}
Write-Host ""; Write-Host "ROLLBACK CONCLUIDO. Estado: V0.9.0-alpha6."; Write-Host ""
