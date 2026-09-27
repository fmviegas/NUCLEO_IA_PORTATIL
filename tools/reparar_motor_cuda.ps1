# NUCLEO IA PORTATIL - REPARO SEGURO DO MOTOR CUDA V0.5
# Restaura somente engine\windows\cuda usando os ZIPs ja existentes em cache\downloads.
# Nao altera modelos, perfis, particoes ou outros dados do SSD.

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ToolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ToolsDir
$CudaDir = Join-Path $Root "engine\windows\cuda"
$Downloads = Join-Path $Root "cache\downloads"

$LlamaZip = Join-Path $Downloads "llama-b10516-bin-win-cuda-12.4-x64.zip"
$CudartZip = Join-Path $Downloads "cudart-llama-bin-win-cuda-12.4-x64.zip"

function Fail([string]$Message) {
    Write-Host ""
    Write-Host "ERRO: $Message" -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "======================================================================"
Write-Host "        NUCLEO IA PORTATIL - REPARO DO MOTOR CUDA V0.5"
Write-Host "======================================================================"
Write-Host ""
Write-Host "Este reparo:"
Write-Host "  - preserva a pasta CUDA atual com outro nome;"
Write-Host "  - recria somente engine\windows\cuda;"
Write-Host "  - reutiliza os ZIPs ja baixados;"
Write-Host "  - nao toca nos modelos nem nos perfis."
Write-Host ""

if (-not (Test-Path -LiteralPath $LlamaZip)) {
    Fail "Nao encontrei $LlamaZip"
}
if (-not (Test-Path -LiteralPath $CudartZip)) {
    Fail "Nao encontrei $CudartZip"
}
if (-not (Test-Path -LiteralPath (Join-Path $Root "engine\windows"))) {
    Fail "Nao encontrei engine\windows na pasta atual."
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupName = "cuda_corrompido_$Stamp"
$BackupDir = Join-Path (Split-Path $CudaDir -Parent) $BackupName

if (Test-Path -LiteralPath $CudaDir) {
    Write-Host "1/5 - Preservando pasta CUDA atual:"
    Write-Host "      $BackupDir"
    try {
        Rename-Item -LiteralPath $CudaDir -NewName $BackupName
    }
    catch {
        Write-Host ""
        Write-Host "Nao foi possivel renomear a pasta CUDA atual." -ForegroundColor Yellow
        Write-Host "Nenhuma alteracao adicional foi feita."
        Write-Host ""
        Write-Host $_.Exception.Message
        exit 2
    }
}

Write-Host "2/5 - Criando nova pasta CUDA..."
New-Item -ItemType Directory -Force -Path $CudaDir | Out-Null

$Temp1 = Join-Path $env:TEMP ("nucleo_cuda_" + [guid]::NewGuid().ToString("N"))
$Temp2 = Join-Path $env:TEMP ("nucleo_cudart_" + [guid]::NewGuid().ToString("N"))

try {
    New-Item -ItemType Directory -Force -Path $Temp1,$Temp2 | Out-Null

    Write-Host "3/5 - Extraindo llama.cpp CUDA..."
    Expand-Archive -LiteralPath $LlamaZip -DestinationPath $Temp1 -Force

    Get-ChildItem -LiteralPath $Temp1 -Recurse -File | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $CudaDir $_.Name) -Force
    }

    Write-Host "4/5 - Extraindo runtime CUDA..."
    Expand-Archive -LiteralPath $CudartZip -DestinationPath $Temp2 -Force

    Get-ChildItem -LiteralPath $Temp2 -Recurse -File | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $CudaDir $_.Name) -Force
    }
}
finally {
    Remove-Item -LiteralPath $Temp1 -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $Temp2 -Recurse -Force -ErrorAction SilentlyContinue
}

$Cli = Join-Path $CudaDir "llama-cli.exe"
$Bench = Join-Path $CudaDir "llama-bench.exe"
$CudaDll = Join-Path $CudaDir "ggml-cuda.dll"

Write-Host "5/5 - Validando motor restaurado..."

foreach ($File in @($Cli,$Bench,$CudaDll)) {
    if (-not (Test-Path -LiteralPath $File)) {
        Fail "Arquivo esperado nao apareceu: $File"
    }

    try {
        $Hash = Get-FileHash -LiteralPath $File -Algorithm SHA256
        Write-Host ("      OK  {0}  SHA256 {1}" -f (Split-Path $File -Leaf), $Hash.Hash.Substring(0,16))
    }
    catch {
        Fail "Nao foi possivel ler/calcular hash de $File"
    }
}

Write-Host ""
Write-Host "Testando llama-cli.exe --version..."
& $Cli --version
if ($LASTEXITCODE -ne 0) {
    Fail "llama-cli.exe foi restaurado, mas --version retornou erro."
}

Write-Host ""
Write-Host "======================================================================"
Write-Host "REPARO CONCLUIDO COM SUCESSO"
Write-Host "======================================================================"
Write-Host ""
Write-Host "A pasta antiga foi preservada em:"
Write-Host "  $BackupDir"
Write-Host ""
Write-Host "Agora execute:"
Write-Host "  INICIAR_NUCLEO_IA.bat"
Write-Host ""
