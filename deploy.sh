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
FRONTEND_CONTAINER_APP="${FRONTEND_CONTAINER_APP:-facebook-scheduler-cca}"
BACKEND_CONTAINER_APP="${BACKEND_CONTAINER_APP:-api-facebook-schedule-cca}"
CONTAINERAPPS_ENVIRONMENT="${CONTAINERAPPS_ENVIRONMENT:-}"
FRONTEND_TARGET_PORT="${FRONTEND_TARGET_PORT:-3100}"
BACKEND_TARGET_PORT="${BACKEND_TARGET_PORT:-8000}"
TARGET_PORT="${TARGET_PORT:-$FRONTEND_TARGET_PORT}"
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
    OPTIONAL_ENV_VARS+=("${key}=${value}")
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

DEPLOY_TIME="$(date +%s)"
PUBLIC_API_BASE_URL="${NEXT_PUBLIC_FASTAPI_BASE_URL:-https://api.schedule.bookinghome.one}"
CORS_ORIGINS="${CORS_ALLOWED_ORIGINS:-https://schedule.bookinghome.one,https://facebook-scheduler-cca.blueisland-303ddce3.eastus.azurecontainerapps.io,http://localhost:3100,http://127.0.0.1:3100}"

COMMON_ENV_VARS=(
  "APP_ENV=production"
  "DATABASE_URL=${DATABASE_URL}"
  "BROWSER_PROFILE_PATH=/app/var/browser-profile"
  "MEDIA_STORAGE_DIR=/app/var/media"
  "GLOBAL_DAILY_AUTO_LIMIT=$(get_env GLOBAL_DAILY_AUTO_LIMIT)"
  "DEFAULT_MIN_DELAY_SECONDS=$(get_env DEFAULT_MIN_DELAY_SECONDS)"
  "DEFAULT_MAX_DELAY_SECONDS=$(get_env DEFAULT_MAX_DELAY_SECONDS)"
  "RUN_MIGRATIONS=${RUN_MIGRATIONS:-true}"
  "NODE_ENV=production"
  "NEXT_PUBLIC_FASTAPI_BASE_URL=${PUBLIC_API_BASE_URL}"
  "CORS_ALLOWED_ORIGINS=${CORS_ORIGINS}"
  "DEPLOY_TIME=${DEPLOY_TIME}"
)

OPTIONAL_ENV_VARS=()
add_env_if_present AZURE_SERVICE_BUS_CONNECTION_STRING
add_env_if_present AZURE_STORAGE_CONNECTION_STRING

FRONTEND_ENV_VARS=(
  "${COMMON_ENV_VARS[@]}"
  "${OPTIONAL_ENV_VARS[@]}"
  "BACKEND_PORT=8000"
  "FASTAPI_BASE_URL=${PUBLIC_API_BASE_URL}"
  "PORT=${FRONTEND_TARGET_PORT}"
)

BACKEND_ENV_VARS=(
  "${COMMON_ENV_VARS[@]}"
  "${OPTIONAL_ENV_VARS[@]}"
  "BACKEND_PORT=${BACKEND_TARGET_PORT}"
  "FASTAPI_BASE_URL=http://127.0.0.1:${BACKEND_TARGET_PORT}"
  "PORT=${FRONTEND_TARGET_PORT}"
)

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
  --build-arg "NEXT_PUBLIC_FASTAPI_BASE_URL=${PUBLIC_API_BASE_URL}" \
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

deploy_container_app() {
  local container_app="$1"
  local target_port="$2"
  local app_role="$3"
  local env_vars=()

  if [ "$app_role" = "frontend" ]; then
    env_vars=("${FRONTEND_ENV_VARS[@]}")
  else
    env_vars=("${BACKEND_ENV_VARS[@]}")
  fi

  if az containerapp show --name "$container_app" --resource-group "$RG" >/dev/null 2>&1; then
    echo "🚀 Updating Container App: ${container_app}..."
    az_with_retry az containerapp update \
      --name "$container_app" \
      --resource-group "$RG" \
      --image "$WEB_IMAGE" \
      --set-env-vars "${env_vars[@]}" \
      >/dev/null

    echo "🌐 Updating ingress target port for ${container_app}: ${target_port}..."
    az_with_retry az containerapp ingress update \
      --name "$container_app" \
      --resource-group "$RG" \
      --target-port "$target_port" \
      --transport auto \
      >/dev/null
  else
    echo "🚀 Container App not found. Creating: ${container_app}..."
    az_with_retry az containerapp create \
      --name "$container_app" \
      --resource-group "$RG" \
      --environment "$CONTAINERAPPS_ENVIRONMENT" \
      --image "$WEB_IMAGE" \
      --ingress external \
      --target-port "$target_port" \
      --transport auto \
      --min-replicas "$MIN_REPLICAS" \
      --max-replicas "$MAX_REPLICAS" \
      --cpu "$CPU" \
      --memory "$MEMORY" \
      "${REGISTRY_ARGS[@]}" \
      --env-vars "${env_vars[@]}" \
      >/dev/null
  fi
}

deploy_container_app "$FRONTEND_CONTAINER_APP" "$FRONTEND_TARGET_PORT" frontend
deploy_container_app "$BACKEND_CONTAINER_APP" "$BACKEND_TARGET_PORT" backend

echo ""
echo "✅ Deploy complete!"
echo "   📦 Image: ${WEB_IMAGE}"
for container_app in "$FRONTEND_CONTAINER_APP" "$BACKEND_CONTAINER_APP"; do
  app_fqdn="$(az containerapp show --name "$container_app" --resource-group "$RG" --query properties.configuration.ingress.fqdn -o tsv)"
  echo "   🌐 ${container_app}: https://${app_fqdn}"
done
