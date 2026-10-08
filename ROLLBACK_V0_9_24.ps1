$ErrorActionPreference="Stop"; $Root=Split-Path -Parent $MyInvocation.MyCommand.Path
function Fail($m){Write-Host "";Write-Host "ERRO: $m" -ForegroundColor Red;exit 1}
$L=Get-ChildItem (Join-Path $Root "backup") -Directory -EA SilentlyContinue|?{$_.Name -like "pre_v0_9_24_final_*"}|Sort-Object Name -Descending|Select-Object -First 1
if(-not $L){Fail "backup pre_v0_9_24_final_* nao encontrado"}
$a=Read-Host "Reverter a consolidacao V0.9.24 (rotulo/VERSION)? [S/n]"; if($a -and $a.ToLowerInvariant() -notin @("s","sim","y","yes")){Write-Host "Cancelado.";exit 0}
$s=Join-Path $L.FullName "VERSION.json"; if(Test-Path -LiteralPath $s){Copy-Item $s (Join-Path $Root "VERSION.json") -Force; Write-Host "restaurado: VERSION.json"}
# index.html: so troca o rotulo (o do backup ainda tinha a aba Planilhas, ja removida)
$ih=Join-Path $Root "ui\index.html"; $t=[IO.File]::ReadAllText($ih,[Text.Encoding]::UTF8); [IO.File]::WriteAllText($ih,$t.Replace("V0.9.24","V0.9.23"),(New-Object Text.UTF8Encoding $false)); Write-Host "rotulo: ui\index.html -> V0.9.23"
$st=Join-Path $Root "state\v0_9_24_final_install.json"; if(Test-Path -LiteralPath $st){Remove-Item -LiteralPath $st -Force}
Write-Host "";Write-Host "ROLLBACK CONCLUIDO. Rotulo/VERSION voltam a V0.9.23; o codigo (fix do exportador xlsx, limite de 50 MB) permanece.";Write-Host ""
