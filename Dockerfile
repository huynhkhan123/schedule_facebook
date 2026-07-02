# syntax=docker/dockerfile:1.7

FROM node:26-bookworm-slim AS frontend-deps
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

FROM node:26-bookworm-slim AS frontend-builder
WORKDIR /app/frontend
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=frontend-deps /app/frontend/node_modules ./node_modules
COPY frontend ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS backend-builder
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
COPY alembic.ini ./
RUN uv sync --frozen --no-dev

FROM node:26-bookworm-slim AS node-runtime

FROM python:3.12-slim-bookworm AS web
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production \
    PORT=3100

RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates libatomic1 \
  && rm -rf /var/lib/apt/lists/*
COPY --from=node-runtime /usr/local/bin/node /usr/local/bin/node

COPY --from=backend-builder /app/.venv ./.venv
COPY --from=backend-builder /app/src ./src
COPY --from=backend-builder /app/alembic.ini ./alembic.ini
COPY src/facebook_group_tool/infrastructure/database/migrations ./src/facebook_group_tool/infrastructure/database/migrations

COPY --from=frontend-builder /app/frontend/.next/standalone ./frontend
COPY --from=frontend-builder /app/frontend/.next/static ./frontend/.next/static
COPY --from=frontend-builder /app/frontend/public ./frontend/public

COPY scripts/start-container.sh ./scripts/start-container.sh
RUN chmod +x ./scripts/start-container.sh \
  && mkdir -p /app/var/browser-profile /app/var/media

EXPOSE 3100
CMD ["./scripts/start-container.sh"]
