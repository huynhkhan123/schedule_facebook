#!/usr/bin/env bash
set -euo pipefail

export APP_ENV="${APP_ENV:-production}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"
export FASTAPI_BASE_URL="${FASTAPI_BASE_URL:-http://127.0.0.1:${BACKEND_PORT}}"
export HOSTNAME="0.0.0.0"
export PORT="${PORT:-3100}"
export BROWSER_PROFILE_PATH="${BROWSER_PROFILE_PATH:-/app/var/browser-profile}"
export MEDIA_STORAGE_DIR="${MEDIA_STORAGE_DIR:-/app/var/media}"

if [ "$PORT" = "$BACKEND_PORT" ]; then
  echo "❌ PORT and BACKEND_PORT must be different; Next.js and FastAPI cannot both bind ${PORT}."
  exit 1
fi

mkdir -p "$BROWSER_PROFILE_PATH" "$MEDIA_STORAGE_DIR"

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "🔁 Running database migrations..."
  alembic -c alembic.ini upgrade head
fi

echo "🚀 Starting FastAPI backend on 0.0.0.0:${BACKEND_PORT}..."
uvicorn facebook_group_tool.main:app --host 0.0.0.0 --port "$BACKEND_PORT" &
BACKEND_PID=$!

echo "🌐 Starting Next.js admin on 0.0.0.0:${PORT}..."
node /app/frontend/server.js --hostname 0.0.0.0 &
FRONTEND_PID=$!

cleanup() {
  echo "🛑 Shutting down container processes..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup TERM INT

wait -n "$BACKEND_PID" "$FRONTEND_PID"
EXIT_CODE=$?
cleanup
exit "$EXIT_CODE"
