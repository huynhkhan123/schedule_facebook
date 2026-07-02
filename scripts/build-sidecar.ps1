$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$ResourceDir = Join-Path $RootDir "desktop\resources\sidecar"
$BrowserResourceDir = Join-Path $RootDir "desktop\resources\ms-playwright"

foreach ($Path in @($ResourceDir, $BrowserResourceDir)) {
  if (Test-Path $Path) {
    Remove-Item -Recurse -Force $Path
  }
  New-Item -ItemType Directory -Force $Path | Out-Null
}

Set-Location $RootDir
$env:PLAYWRIGHT_BROWSERS_PATH = $BrowserResourceDir

$UseUv = [bool](Get-Command uv -ErrorAction SilentlyContinue)
$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"
if (-not $UseUv -and -not (Test-Path $VenvPython)) {
  throw "Neither uv nor .venv\Scripts\python.exe is available. Run 'uv sync --all-groups' first."
}

function Invoke-ProjectPython {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

  if ($UseUv) {
    & uv run python @Arguments
  } else {
    & $VenvPython @Arguments
  }
}

function Invoke-ProjectPyInstaller {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

  if ($UseUv) {
    & uv run pyinstaller @Arguments
  } else {
    & $VenvPython -m PyInstaller @Arguments
  }
}

Invoke-ProjectPython -m playwright install chromium
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

$RemovePackageBrowsersScript = "from pathlib import Path; import shutil; import playwright; package_browsers = Path(playwright.__file__).parent / 'driver' / 'package' / '.local-browsers'; shutil.rmtree(package_browsers) if package_browsers.exists() else None"
Invoke-ProjectPython -c $RemovePackageBrowsersScript
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Invoke-ProjectPyInstaller `
  --clean `
  --name facebook-group-connector-sidecar `
  --onefile `
  --paths (Join-Path $RootDir "src") `
  --distpath $ResourceDir `
  --workpath (Join-Path $RootDir "build\pyinstaller") `
  --specpath (Join-Path $RootDir "build\pyinstaller") `
  (Join-Path $RootDir "src\facebook_group_tool\connector\sidecar.py")
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

$SidecarExe = Join-Path $ResourceDir "facebook-group-connector-sidecar.exe"
if (-not (Test-Path $SidecarExe)) {
  throw "Expected sidecar executable was not created: $SidecarExe"
}
