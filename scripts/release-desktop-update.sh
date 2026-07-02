#!/usr/bin/env bash
# Bump desktop version, commit it, tag it, and push the update tag.
# Usage:
#   ./scripts/release-desktop-update.sh          # patch bump, e.g. 0.1.9 -> 0.1.10
#   ./scripts/release-desktop-update.sh 0.2.0    # explicit version
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v git >/dev/null 2>&1; then
  echo "❌ Missing required command: git"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "❌ Missing required command: npm"
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "❌ Missing required command: node"
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "❌ Working tree is not clean. Commit or stash changes before releasing desktop update."
  git status --short
  exit 1
fi

if [ $# -gt 0 ]; then
  npm version "$1" --no-git-tag-version --prefix desktop
else
  npm version patch --no-git-tag-version --prefix desktop
fi

VERSION="$(node -p "require('./desktop/package.json').version")"
TAG="desktop-v${VERSION}"

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "❌ Tag already exists locally: ${TAG}"
  exit 1
fi

if git ls-remote --tags origin "$TAG" | grep -q "$TAG"; then
  echo "❌ Tag already exists on origin: ${TAG}"
  exit 1
fi

git add desktop/package.json desktop/package-lock.json
git commit -m "chore: release desktop ${VERSION}"
git tag "$TAG"
git push origin main
git push origin "$TAG"

echo ""
echo "✅ Desktop update release triggered"
echo "   Version: ${VERSION}"
echo "   Tag:     ${TAG}"
echo "   AppVeyor will build and upload release assets to:"
echo "   https://github.com/huynhkhan123/schedule_facebook/releases/tag/${TAG}"
