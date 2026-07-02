#!/usr/bin/env bash
# Sync every KEY=VALUE entry from a dotenv file to an Azure Container App.
# Usage:
#   ./scripts/sync-env-to-containerapp.sh
#   RG=campaign-rg CONTAINER_APP=facebook-scheduler-cca ENV_FILE=.env ./scripts/sync-env-to-containerapp.sh
set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE="${ENV_FILE:-.env}"
RG="${RG:-campaign-rg}"
CONTAINER_APP="${CONTAINER_APP:-facebook-scheduler-cca}"

if ! command -v az >/dev/null 2>&1; then
  echo "❌ Missing required command: az"
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Env file not found: $ENV_FILE"
  exit 1
fi

trim() {
  local value="$1"
  value="${value#${value%%[![:space:]]*}}"
  value="${value%${value##*[![:space:]]}}"
  printf '%s' "$value"
}

strip_matching_quotes() {
  local value="$1"
  if [[ "$value" == \"*\" && "$value" == *\" ]]; then
    value="${value:1:${#value}-2}"
  elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
    value="${value:1:${#value}-2}"
  fi
  printf '%s' "$value"
}

ENV_VARS=()
LINE_NUMBER=0

while IFS= read -r raw_line || [ -n "$raw_line" ]; do
  LINE_NUMBER=$((LINE_NUMBER + 1))
  line="$(trim "$raw_line")"

  if [ -z "$line" ] || [[ "$line" == \#* ]]; then
    continue
  fi

  if [[ "$line" == export\ * ]]; then
    line="$(trim "${line#export }")"
  fi

  if [[ "$line" != *=* ]]; then
    echo "⚠️  Skipping line ${LINE_NUMBER}: missing '='"
    continue
  fi

  key="$(trim "${line%%=*}")"
  value="$(trim "${line#*=}")"

  if [[ ! "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    echo "⚠️  Skipping line ${LINE_NUMBER}: invalid env key '$key'"
    continue
  fi

  value="$(strip_matching_quotes "$value")"
  ENV_VARS+=("${key}=${value}")
done < "$ENV_FILE"

if [ "${#ENV_VARS[@]}" -eq 0 ]; then
  echo "❌ No env vars found in $ENV_FILE"
  exit 1
fi

echo "🔐 Checking Azure login..."
az account show >/dev/null

echo "📦 Checking Container App: ${CONTAINER_APP} in resource group ${RG}..."
az containerapp show \
  --name "$CONTAINER_APP" \
  --resource-group "$RG" \
  >/dev/null

echo "⬆️  Syncing ${#ENV_VARS[@]} env vars from ${ENV_FILE} to ${CONTAINER_APP}..."
az containerapp update \
  --name "$CONTAINER_APP" \
  --resource-group "$RG" \
  --set-env-vars "${ENV_VARS[@]}" \
  >/dev/null

echo "✅ Env sync complete: ${CONTAINER_APP}"
echo "🔁 Azure Container Apps will create a new revision if revision mode/settings require it."
