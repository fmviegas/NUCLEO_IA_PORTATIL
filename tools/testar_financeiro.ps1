# testar_financeiro.ps1 — testa um ControleFinanceiro*.xlsx NO EXCEL (COM), com dados ficticios.
# Uso: powershell -File tools\testar_financeiro.ps1 -Arquivo <xlsx> -Saida <json> [-PdfDir <pasta>]
# Requer Microsoft Excel instalado. Nao altera o arquivo de entrada (trabalha numa copia).
param([Parameter(Mandatory=$true)][string]$Arquivo,
      [Parameter(Mandatory=$true)][string]$Saida,
      [string]$PdfDir = "")
$ErrorActionPreference = "Stop"
$res = [ordered]@{ arquivo = $Arquivo; checks = @(); erros_vazio = @{}; erros_dados = @{}; graficos = @{}; formas = @{} }
function Check($item, $nome, $ok, $det = "") { $script:res.checks += [ordered]@{ item = $item; nome = $nome; ok = [bool]$ok; detalhe = "$det" } }
function Perto($a, $b) { try { return [math]::Abs([double]$a - [double]$b) -lt 0.005 } catch { return $false } }

$tmp = Join-Path $env:TEMP ("fin_teste_" + [guid]::NewGuid().ToString("N") + ".xlsx")
Copy-Item -LiteralPath $Arquivo -Destination $tmp
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false; $xl.ScreenUpdating = $false
try {
  $wb = $xl.Workbooks.Open($tmp)
  $xl.CalculateFull()
  $nomes = @(); foreach ($ws in $wb.Worksheets) { $nomes += $ws.Name }
  $res.abas = $nomes
  $esperadas = @("Início","Contas e Cadastro","Evolução","C.Crédito","Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez")
  $ok1 = ($nomes.Count -ge 16) -and ((@($nomes[0..15]) -join "|") -eq ($esperadas -join "|"))
  Check 1 "16 abas na ordem" $ok1 (($nomes -join ", "))

  function ContaErros() {
    $m = @{}
    foreach ($ws in $wb.Worksheets) {
      $n = 0
      try { $n = $ws.UsedRange.SpecialCells(-4123, 16).Count } catch { $n = 0 }
      if ($n -gt 0) { $m[$ws.Name] = $n }
    }
    return $m
  }
  $res.erros_vazio = ContaErros
  foreach ($ws in $wb.Worksheets) {
    $res.graficos[$ws.Name] = $ws.ChartObjects().Count
    $res.formas[$ws.Name] = $ws.Shapes.Count
  }
  $prot = @(); foreach ($ws in $wb.Worksheets) { if ($esperadas -contains $ws.Name -and -not $ws.ProtectContents) { $prot += $ws.Name } }
  Check 8 "protecao mantida nas 16 abas" ($prot.Count -eq 0) ("desprotegidas: " + ($prot -join ","))

  # ---------- dados ficticios (so celulas de digitacao, desbloqueadas) ----------
  $jan = $wb.Worksheets.Item("Jan"); $fev = $wb.Worksheets.Item("Fev"); $dez = $wb.Worksheets.Item("Dez")
  $jan.Range("E6").Value2 = "Salario"; $jan.Range("F6").Value2 = "Salário"; $jan.Range("G6").Value2 = 5000; $jan.Range("J6").Value2 = "Sim"
  $jan.Range("G7").Value2 = 1000
  $jan.Range("M6").Value2 = "Aluguel"; $jan.Range("N6").Value2 = "Moradia"; $jan.Range("O6").Value2 = 1200; $jan.Range("R6").Value2 = "Não"
  $jan.Range("O7").Value2 = 300
  $jan.Range("U8").Value2 = 500; $jan.Range("U9").Value2 = 1000
  $fev.Range("G6").Value2 = 4000; $fev.Range("O6").Value2 = 4500
  $cc = $wb.Worksheets.Item("C.Crédito")
  $cc.Range("E17").Value2 = "Visa"; $cc.Range("F17").Value2 = "TV"; $cc.Range("G17").Value2 = 1200; $cc.Range("H17").Value2 = 3
  $cc.Range("I17").Value2 = 400; $cc.Range("J17").Value2 = 400; $cc.Range("K17").Value2 = 400
  $cc.Range("G18").Value2 = 900; $cc.Range("I18").Value2 = 300; $cc.Range("J18").Value2 = 300
  $ct = $wb.Worksheets.Item("Contas e Cadastro")
  $ct.Range("D4").Value2 = "Banco X"; $ct.Range("E4").Value2 = 1000; $ct.Range("F4").Value2 = 500; $ct.Range("G4").Value2 = 200
  $ct.Range("J4").Value2 = 100; $ct.Range("K4").Value2 = 50
  $xl.CalculateFull()

  $v = { param($ws, $c) $ws.Range($c).Value2 }
  Check 2 "Jan totais (U5=6000, U6=1500, U7=4500)" ((Perto (& $v $jan "U5") 6000) -and (Perto (& $v $jan "U6") 1500) -and (Perto (& $v $jan "U7") 4500)) ("U5={0} U6={1} U7={2}" -f (& $v $jan "U5"), (& $v $jan "U6"), (& $v $jan "U7"))
  Check 2 "Jan percentuais (I6=83,33%, Q6=80%)" ((Perto (& $v $jan "I6") (5000/6000)) -and (Perto (& $v $jan "Q6") 0.8)) ("I6={0} Q6={1}" -f (& $v $jan "I6"), (& $v $jan "Q6"))
  # no original, linha vazia mostra 0% (G8/G56 = 0) — o que importa e' nao dar erro
  Check 2 "linha vazia sem erro (I8 e Q8 = 0%)" ((Perto (& $v $jan "I8") 0) -and (Perto (& $v $jan "Q8") 0)) ("I8='{0}' Q8='{1}'" -f (& $v $jan "I8"), (& $v $jan "Q8"))
  Check 3 "Jan U10 = (U7+U9)-U8 = 5000" (Perto (& $v $jan "U10") 5000) ("U10={0}" -f (& $v $jan "U10"))
  Check 3 "Fev U9 = Jan U10 e U10 = 4500" ((Perto (& $v $fev "U9") 5000) -and (Perto (& $v $fev "U10") 4500)) ("U9={0} U10={1}" -f (& $v $fev "U9"), (& $v $fev "U10"))
  Check 3 "saldo chega a Dez (U9=U10=4500)" ((Perto (& $v $dez "U9") 4500) -and (Perto (& $v $dez "U10") 4500)) ("Dez U9={0} U10={1}" -f (& $v $dez "U9"), (& $v $dez "U10"))
  $ev = $wb.Worksheets.Item("Evolução")
  Check 4 "Evolucao entradas/saidas/liquido e totais" ((Perto (& $v $ev "E39") 6000) -and (Perto (& $v $ev "S39") 10000) -and (Perto (& $v $ev "S40") 6000) -and (Perto (& $v $ev "F41") -500) -and (Perto (& $v $ev "S41") 4000)) ("E39={0} S39={1} S40={2} F41={3} S41={4}" -f (& $v $ev "E39"), (& $v $ev "S39"), (& $v $ev "S40"), (& $v $ev "F41"), (& $v $ev "S41"))
  Check 4 "Evolucao investido acumulado (E42=F42=P42=500) e saldo (E43=5000, F43=4500)" ((Perto (& $v $ev "E42") 500) -and (Perto (& $v $ev "F42") 500) -and (Perto (& $v $ev "P42") 500) -and (Perto (& $v $ev "E43") 5000) -and (Perto (& $v $ev "F43") 4500)) ("E42={0} F42={1} P42={2} E43={3} F43={4}" -f (& $v $ev "E42"), (& $v $ev "F42"), (& $v $ev "P42"), (& $v $ev "E43"), (& $v $ev "F43"))
  Check 5 "cartao U17=1200, U18=600, U117=1800" ((Perto (& $v $cc "U17") 1200) -and (Perto (& $v $cc "U18") 600) -and (Perto (& $v $cc "U117") 1800)) ("U17={0} U18={1} U117={2}" -f (& $v $cc "U17"), (& $v $cc "U18"), (& $v $cc "U117"))
  Check 6 "contas H4=1300, I4=1300, L4=1350, AZ4=1350" ((Perto (& $v $ct "H4") 1300) -and (Perto (& $v $ct "I4") 1300) -and (Perto (& $v $ct "L4") 1350) -and (Perto (& $v $ct "AZ4") 1350)) ("H4={0} I4={1} L4={2} AZ4={3}" -f (& $v $ct "H4"), (& $v $ct "I4"), (& $v $ct "L4"), (& $v $ct "AZ4"))

  $res.erros_dados = ContaErros
  Check 7 "nenhum erro (#DIV/0!, #REF!...) vazio e com dados" (($res.erros_vazio.Count -eq 0) -and ($res.erros_dados.Count -eq 0)) ("vazio: " + (($res.erros_vazio.Keys | % { "$_=$($res.erros_vazio[$_])" }) -join ",") + " | dados: " + (($res.erros_dados.Keys | % { "$_=$($res.erros_dados[$_])" }) -join ","))

  # ---------- so na aprimorada ----------
  if ($nomes -contains "Notas") {
    $titulos = @(); $i = 0
    foreach ($m in @("Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez")) { $titulos += $wb.Worksheets.Item($m).Range("D2").Text }
    Check "A" "titulos D2 por mes" ((($titulos -join "|") -eq "JANEIRO|FEVEREIRO|MARÇO|ABRIL|MAIO|JUNHO|JULHO|AGOSTO|SETEMBRO|OUTUBRO|NOVEMBRO|DEZEMBRO")) ($titulos -join ",")
    $dv = @(); foreach ($c in @("F6","N55","J6","R30")) { try { $dv += "$c=" + $jan.Range($c).Validation.Type } catch { $dv += "$c=nenhuma" } }
    Check "A" "listas suspensas (Validation.Type=3)" (($dv | ? { $_ -notmatch "=3$" }).Count -eq 0) ($dv -join " ")
    Check "A" "conferencia cartao V17=OK, V18=Difere, V117='1 difere(m)'" ((& $v $cc "V17") -eq "OK" -and (& $v $cc "V18") -eq "Difere R$ 300,00" -and (& $v $cc "V117") -eq "1 difere(m)") ("V17={0} | V18={1} | V117={2}" -f (& $v $cc "V17"), (& $v $cc "V18"), (& $v $cc "V117"))
    $fc = @(); foreach ($p in @(@("Jan","U10"),@("Jan","O6"),@("Evolução","F41"),@("Contas e Cadastro","H4"),@("C.Crédito","V18"))) { $fc += ("{0}!{1}={2}" -f $p[0], $p[1], $wb.Worksheets.Item($p[0]).Range($p[1]).FormatConditions.Count) }
    Check "A" "destaques condicionais presentes" (($fc | ? { $_ -match "=0$" }).Count -eq 0) ($fc -join " ")
    # destaque efetivo: Fev U10 negativo? (Fev U7=-500) -> cor exibida
    $res.cor_fev_U7 = $fev.Range("U7").DisplayFormat.Font.Color
    $res.cor_jan_O6 = $jan.Range("O6").DisplayFormat.Font.Color
    $fev.Range("U8").Value2 = 6000; $xl.CalculateFull()
    $res.fill_fev_U10_neg = $fev.Range("U10").DisplayFormat.Interior.Color
    $res.fev_U10_neg = $fev.Range("U10").Value2
  }

  if ($PdfDir) {
    New-Item -ItemType Directory -Force -Path $PdfDir | Out-Null
    foreach ($n in @("Início","Evolução","Jan","Fev","C.Crédito","Contas e Cadastro","Notas")) {
      if ($nomes -contains $n) {
        $safe = ($n -replace "[^A-Za-z0-9]", "_")
        try { $wb.Worksheets.Item($n).ExportAsFixedFormat(0, (Join-Path $PdfDir "$safe.pdf")) } catch { $res["pdf_erro_$safe"] = "$_" }
      }
    }
  }
  $wb.Close($false)
} catch {
  $res.excecao = "$_"
} finally {
  $xl.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($xl)
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}
$res | ConvertTo-Json -Depth 6 | Out-File -FilePath $Saida -Encoding utf8
