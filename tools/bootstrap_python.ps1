# NUCLEO IA PORTATIL - Bootstrap V0.5
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ToolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ToolsDir
$RuntimeDir = Join-Path $Root "runtime\python"
$PythonExe = Join-Path $RuntimeDir "python.exe"
$CacheDir = Join-Path $Root "cache\downloads"
$ZipPath = Join-Path $CacheDir "python-3.13.13-embed-amd64.zip"

$Url = "https://www.python.org/ftp/python/3.13.13/python-3.13.13-embed-amd64.zip"
$ExpectedSha256 = "8766a8775746235e23cf5aee5027ab1060bb981d93110577adcf3508aa0cbd55"

if (Test-Path $PythonExe) {
    Write-Host "Runtime Python portatil ja existe."
    exit 0
}

New-Item -ItemType Directory -Force -Path $RuntimeDir,$CacheDir | Out-Null

Write-Host ""
Write-Host "NUCLEO IA PORTATIL V0.5"
Write-Host "Preparando Python portatil no SSD..."
Write-Host "Fonte: Python Software Foundation"
Write-Host ""

if (-not (Test-Path $ZipPath)) {
    $Curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($Curl) {
        & curl.exe -L --fail --retry 4 --retry-delay 3 --output $ZipPath $Url
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao baixar o runtime Python."
        }
    }
    else {
        Invoke-WebRequest -Uri $Url -OutFile $ZipPath -UseBasicParsing
    }
}

$Actual = (Get-FileHash -Algorithm SHA256 -Path $ZipPath).Hash.ToLowerInvariant()
if ($Actual -ne $ExpectedSha256) {
    Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue
    throw "SHA256 do Python portatil nao confere. Download removido."
}

Write-Host "SHA256 OK."
Write-Host "Extraindo runtime..."

# Limpa apenas o runtime Python incompleto, nunca modelos/engine.
Get-ChildItem -Path $RuntimeDir -Force -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Expand-Archive -Path $ZipPath -DestinationPath $RuntimeDir -Force

if (-not (Test-Path $PythonExe)) {
    throw "python.exe nao apareceu apos a extracao."
}

$Info = [PSCustomObject]@{
    project = "NUCLEO IA PORTATIL"
    version = "0.5"
    python_version = "3.13.13"
    architecture = "amd64"
    installed_at = (Get-Date).ToString("o")
    source = "Python Software Foundation"
    sha256 = $ExpectedSha256
}
$Info | ConvertTo-Json -Depth 3 |
    Set-Content (Join-Path $Root "config\runtime_python_v0_5.json") -Encoding UTF8

Write-Host "Runtime portatil pronto."
exit 0
