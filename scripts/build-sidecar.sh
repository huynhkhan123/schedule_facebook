#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESOURCE_DIR="$ROOT_DIR/desktop/resources/sidecar"
BROWSER_RESOURCE_DIR="$ROOT_DIR/desktop/resources/ms-playwright"

rm -rf "$RESOURCE_DIR" "$BROWSER_RESOURCE_DIR"
mkdir -p "$RESOURCE_DIR" "$BROWSER_RESOURCE_DIR"

cd "$ROOT_DIR"
export PLAYWRIGHT_BROWSERS_PATH="$BROWSER_RESOURCE_DIR"

if command -v uv >/dev/null 2>&1; then
  PYTHON_RUNNER=(uv run python)
  PYINSTALLER_RUNNER=(uv run pyinstaller)
else
  PYTHON_RUNNER=(".venv/bin/python")
  PYINSTALLER_RUNNER=(".venv/bin/python" -m PyInstaller)
fi

"${PYTHON_RUNNER[@]}" -m playwright install chromium
"${PYTHON_RUNNER[@]}" - <<'PY'
from pathlib import Path
import playwright

package_browsers = Path(playwright.__file__).parent / "driver" / "package" / ".local-browsers"
if package_browsers.exists():
    import shutil
    shutil.rmtree(package_browsers)
PY

"${PYINSTALLER_RUNNER[@]}" \
  --clean \
  --name facebook-group-connector-sidecar \
  --onefile \
  --paths "$ROOT_DIR/src" \
  --distpath "$RESOURCE_DIR" \
  --workpath "$ROOT_DIR/build/pyinstaller" \
  --specpath "$ROOT_DIR/build/pyinstaller" \
  "$ROOT_DIR/src/facebook_group_tool/connector/sidecar.py"

test -x "$RESOURCE_DIR/facebook-group-connector-sidecar"
