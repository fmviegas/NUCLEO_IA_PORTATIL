# excel_ler.ps1 — abre um .xlsx no Excel (COM), recalcula e devolve valores de celulas.
# Uso: powershell -File tools\excel_ler.ps1 -Arquivo <xlsx> -Celulas <json: ["Aba!A1", ...]> -Saida <json>
# Le uma COPIA (o arquivo original nao e' alterado). Requer Microsoft Excel.
param([Parameter(Mandatory=$true)][string]$Arquivo,
      [Parameter(Mandatory=$true)][string]$Celulas,
      [Parameter(Mandatory=$true)][string]$Saida)
$ErrorActionPreference = "Stop"
$refs = Get-Content -LiteralPath $Celulas -Raw -Encoding UTF8 | ConvertFrom-Json
$tmp = Join-Path $env:TEMP ("xl_ler_" + [guid]::NewGuid().ToString("N") + ".xlsx")
Copy-Item -LiteralPath $Arquivo -Destination $tmp
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false
$res = [ordered]@{ valores = [ordered]@{}; erros = 0; excecao = $null }
try {
  $wb = $xl.Workbooks.Open($tmp)
  $xl.CalculateFull()
  foreach ($r in $refs) {
    $aba, $cel = $r -split "!", 2
    $v = $wb.Worksheets.Item($aba).Range($cel).Value2
    if ($v -is [int] -and $v -lt -2146820000) { $res.erros++ }
    $res.valores[$r] = $v
  }
  foreach ($ws in $wb.Worksheets) { try { $res.erros += $ws.UsedRange.SpecialCells(-4123, 16).Count } catch { } }
  $wb.Close($false)
} catch { $res.excecao = "$_" }
finally { $xl.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($xl); Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue }
$res | ConvertTo-Json -Depth 4 | Out-File -FilePath $Saida -Encoding utf8
