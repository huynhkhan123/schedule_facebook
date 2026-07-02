$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$DesktopDir = Join-Path $RootDir "desktop"
$DistDir = Join-Path $RootDir "dist\desktop"
$Repository = $env:GITHUB_REPOSITORY

if ([string]::IsNullOrWhiteSpace($Repository)) {
  $Repository = "huynhkhan123/schedule_facebook"
}

function Require-Command {
  param([string]$Name)

  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Missing required command: $Name"
  }
}

Require-Command "git"
Require-Command "gh"
Require-Command "node"
Require-Command "npm"
Require-Command "uv"

$Version = node -p "require('$($DesktopDir.Replace('\', '\\'))/package.json').version"
$Tag = "desktop-v$Version"

Write-Host "🔎 Releasing Windows desktop $Version to $Repository ($Tag)"

$ExistingTag = git -C $RootDir tag --list $Tag
if ([string]::IsNullOrWhiteSpace($ExistingTag)) {
  throw "Git tag $Tag does not exist locally. Create it first: git tag $Tag"
}

Write-Host "🔐 Checking GitHub CLI authentication..."
gh auth status

Write-Host "📦 Installing desktop dependencies..."
Set-Location $DesktopDir
npm ci

Write-Host "✅ Type-checking desktop app..."
npm run typecheck

Write-Host "🧪 Running connector unit tests..."
Set-Location $RootDir
uv run pytest tests/unit/test_connector_core.py tests/unit/test_connector_sidecar.py -v

Write-Host "🐍 Building Windows sidecar..."
& (Join-Path $RootDir "scripts\build-sidecar.ps1")

Write-Host "🪟 Building unsigned Windows installer..."
Set-Location $DesktopDir
$env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
npm run dist:win

$Assets = @()
$Assets += Get-ChildItem -Path $DistDir -Filter "*.exe" -File
$Assets += Get-ChildItem -Path $DistDir -Filter "*.blockmap" -File
$LatestYml = Join-Path $DistDir "latest.yml"
if (Test-Path $LatestYml) {
  $Assets += Get-Item $LatestYml
}

if ($Assets.Count -eq 0) {
  throw "No release assets found in $DistDir"
}

if (-not (Test-Path $LatestYml)) {
  throw "Missing latest.yml in $DistDir. electron-updater requires this file."
}

Write-Host "🚀 Creating/updating GitHub Release $Tag..."
$ReleaseExists = $true
gh release view $Tag --repo $Repository *> $null
if ($LASTEXITCODE -ne 0) {
  $ReleaseExists = $false
}

if (-not $ReleaseExists) {
  gh release create $Tag --repo $Repository --title "Facebook Group Connector $Version" --notes "Windows unsigned test release $Version. Customers may see Windows SmartScreen / Unknown Publisher warnings."
}

Write-Host "📤 Uploading release assets..."
$AssetPaths = $Assets | ForEach-Object { $_.FullName }
gh release upload $Tag --repo $Repository --clobber @AssetPaths

Write-Host ""
Write-Host "✅ Windows desktop release uploaded"
Write-Host "   Tag:     $Tag"
Write-Host "   Release: https://github.com/$Repository/releases/tag/$Tag"
Write-Host "   Assets:"
$Assets | ForEach-Object { Write-Host "   - $($_.Name)" }
