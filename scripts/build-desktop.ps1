$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")

& (Join-Path $RootDir "scripts\build-sidecar.ps1")
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Set-Location (Join-Path $RootDir "desktop")
npm run dist -- --win nsis x64
exit $LASTEXITCODE
