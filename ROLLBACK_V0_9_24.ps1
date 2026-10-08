$ErrorActionPreference="Stop"; $Root=Split-Path -Parent $MyInvocation.MyCommand.Path
function Fail($m){Write-Host "";Write-Host "ERRO: $m" -ForegroundColor Red;exit 1}
$L=Get-ChildItem (Join-Path $Root "backup") -Directory -EA SilentlyContinue|?{$_.Name -like "pre_v0_9_24_final_*"}|Sort-Object Name -Descending|Select-Object -First 1
if(-not $L){Fail "backup pre_v0_9_24_final_* nao encontrado"}
$a=Read-Host "Reverter a consolidacao V0.9.24 (rotulo/VERSION)? [S/n]"; if($a -and $a.ToLowerInvariant() -notin @("s","sim","y","yes")){Write-Host "Cancelado.";exit 0}
foreach($rel in @("VERSION.json","ui\index.html")){$s=Join-Path $L.FullName $rel; if(Test-Path -LiteralPath $s){Copy-Item $s (Join-Path $Root $rel) -Force; Write-Host "restaurado: $rel"}}
$st=Join-Path $Root "state\v0_9_24_final_install.json"; if(Test-Path -LiteralPath $st){Remove-Item -LiteralPath $st -Force}
Write-Host "";Write-Host "ROLLBACK CONCLUIDO. Rotulo volta a V0.9.23; o codigo (planilhas) permanece.";Write-Host ""
