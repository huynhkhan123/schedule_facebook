#!/usr/bin/env bash
# Build & deploy the FastAPI + Next.js admin app to Azure Container Apps.
# Usage: ./deploy.sh
set -euo pipefail

cd "$(dirname "$0")"

ENV_FILE=".env"
RG="${RG:-campaign-rg}"
REGISTRY_NAME="${REGISTRY_NAME:-sendmailapp}"
REGISTRY="${REGISTRY:-${REGISTRY_NAME}.azurecr.io}"
IMAGE_NAME="${IMAGE_NAME:-facebook-group-tool}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
WEB_IMAGE="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
CONTAINER_APP="${CONTAINER_APP:-facebook-scheduler-cca}"
CONTAINERAPPS_ENVIRONMENT="${CONTAINERAPPS_ENVIRONMENT:-}"
TARGET_PORT="${TARGET_PORT:-3100}"
MIN_REPLICAS="${MIN_REPLICAS:-0}"
MAX_REPLICAS="${MAX_REPLICAS:-1}"
CPU="${CPU:-1.0}"
MEMORY="${MEMORY:-2Gi}"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ .env file not found"
  exit 1
fi

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

get_env() {
  local key="$1"
  local value
  value=$(grep -E "^${key}=" "$ENV_FILE" | tail -n 1 | cut -d= -f2- || true)
  value="${value%\"}"
  value="${value#\"}"
  value="${value%\'}"
  value="${value#\'}"
  printf '%s' "$value"
}

add_env_if_present() {
  local key="$1"
  local value
  value="$(get_env "$key")"
  if [ -n "$value" ]; then
    ENV_VARS+=("${key}=${value}")
  fi
}

require_env() {
  local key="$1"
  local value
  value="$(get_env "$key")"
  if [ -z "$value" ]; then
    echo "❌ Missing required env var in ${ENV_FILE}: ${key}"
    exit 1
  fi
  printf '%s' "$value"
}

az_with_retry() {
  local attempt=1
  local max_attempts=3
  local delay_seconds=8

  until "$@"; do
    if [ "$attempt" -ge "$max_attempts" ]; then
      echo "❌ Azure CLI command failed after ${max_attempts} attempts: $*"
      return 1
    fi

    echo "⚠️  Azure CLI command failed, retrying in ${delay_seconds}s (${attempt}/${max_attempts})..."
    sleep "$delay_seconds"
    attempt=$((attempt + 1))
    delay_seconds=$((delay_seconds * 2))
  done
}

for binary in az docker npm; do
  if ! command_exists "$binary"; then
    echo "❌ Missing required command: $binary"
    exit 1
  fi
done

DATABASE_URL="$(require_env DATABASE_URL)"
CONTAINERAPPS_ENVIRONMENT="${CONTAINERAPPS_ENVIRONMENT:-$(get_env AZURE_CONTAINERAPPS_ENVIRONMENT)}"
CONTAINERAPPS_ENVIRONMENT="${CONTAINERAPPS_ENVIRONMENT:-campaign-env}"

ENV_VARS=(
  "APP_ENV=production"
  "DATABASE_URL=${DATABASE_URL}"
  "FASTAPI_BASE_URL=http://127.0.0.1:8000"
  "BROWSER_PROFILE_PATH=/app/var/browser-profile"
  "MEDIA_STORAGE_DIR=/app/var/media"
  "GLOBAL_DAILY_AUTO_LIMIT=$(get_env GLOBAL_DAILY_AUTO_LIMIT)"
  "DEFAULT_MIN_DELAY_SECONDS=$(get_env DEFAULT_MIN_DELAY_SECONDS)"
  "DEFAULT_MAX_DELAY_SECONDS=$(get_env DEFAULT_MAX_DELAY_SECONDS)"
  "RUN_MIGRATIONS=${RUN_MIGRATIONS:-true}"
  "NODE_ENV=production"
  "PORT=${TARGET_PORT}"
  "DEPLOY_TIME=$(date +%s)"
)

add_env_if_present AZURE_SERVICE_BUS_CONNECTION_STRING
add_env_if_present AZURE_STORAGE_CONNECTION_STRING

REGISTRY_ARGS=(--registry-server "$REGISTRY")
ACR_USERNAME="$(az acr credential show --name "$REGISTRY_NAME" --query username -o tsv 2>/dev/null || true)"
ACR_PASSWORD="$(az acr credential show --name "$REGISTRY_NAME" --query 'passwords[0].value' -o tsv 2>/dev/null || true)"
if [ -n "$ACR_USERNAME" ] && [ -n "$ACR_PASSWORD" ]; then
  REGISTRY_ARGS+=(--registry-username "$ACR_USERNAME" --registry-password "$ACR_PASSWORD")
fi

echo "🔐 Checking Azure login..."
az account show >/dev/null

echo "🔐 Logging into ACR: ${REGISTRY_NAME}..."
az acr login --name "$REGISTRY_NAME"

echo "📦 Installing frontend dependencies for a reproducible build context..."
(
  cd frontend
  npm ci
)

echo "🔨 Building image: ${WEB_IMAGE}..."
docker build \
  --platform linux/amd64 \
  --provenance=false \
  --target web \
  -t "$WEB_IMAGE" \
  .

echo "📤 Pushing image to ACR..."
docker push "$WEB_IMAGE"

LOCATION="$(az group show --name "$RG" --query location -o tsv)"

if ! az containerapp env show --name "$CONTAINERAPPS_ENVIRONMENT" --resource-group "$RG" >/dev/null 2>&1; then
  echo "🌱 Container Apps environment not found. Creating: ${CONTAINERAPPS_ENVIRONMENT}..."
  az containerapp env create \
    --name "$CONTAINERAPPS_ENVIRONMENT" \
    --resource-group "$RG" \
    --location "$LOCATION" \
    >/dev/null
fi

if az containerapp show --name "$CONTAINER_APP" --resource-group "$RG" >/dev/null 2>&1; then
  echo "🚀 Updating Container App: ${CONTAINER_APP}..."
  az_with_retry az containerapp update \
    --name "$CONTAINER_APP" \
    --resource-group "$RG" \
    --image "$WEB_IMAGE" \
    --set-env-vars "${ENV_VARS[@]}" \
    >/dev/null
else
  echo "🚀 Container App not found. Creating: ${CONTAINER_APP}..."
  az_with_retry az containerapp create \
    --name "$CONTAINER_APP" \
    --resource-group "$RG" \
    --environment "$CONTAINERAPPS_ENVIRONMENT" \
    --image "$WEB_IMAGE" \
    --ingress external \
    --target-port "$TARGET_PORT" \
    --min-replicas "$MIN_REPLICAS" \
    --max-replicas "$MAX_REPLICAS" \
    --cpu "$CPU" \
    --memory "$MEMORY" \
    "${REGISTRY_ARGS[@]}" \
    --env-vars "${ENV_VARS[@]}" \
    >/dev/null
fi

APP_FQDN="$(az containerapp show --name "$CONTAINER_APP" --resource-group "$RG" --query properties.configuration.ingress.fqdn -o tsv)"

echo ""
echo "✅ Deploy complete!"
echo "   📦 Image: ${WEB_IMAGE}"
echo "   🌐 Web:   https://${APP_FQDN}"
