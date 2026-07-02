# Development Guide

## Setup

```bash
uv sync
cp .env.example .env
uv run playwright install chromium
```

## Run local API

```bash
uv run uvicorn facebook_group_tool.main:app --reload
```

Open `http://127.0.0.1:8000` for the legacy FastAPI/Jinja dashboard.

## Run Next.js admin dashboard

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open `http://127.0.0.1:3100` for the Vietnamese Octo Code admin dashboard. Keep the FastAPI server running on `http://127.0.0.1:8000` because the Next.js UI calls the existing `/api/*` backend endpoints.

## Database migrations

```bash
uv run alembic -c alembic.ini upgrade head
```

The app expects `DATABASE_URL` to point to PostgreSQL. Do not configure SQLite for this project.

For destructive integration repository tests, use a separate `DATABASE_URL_TEST`. Do not point `DATABASE_URL_TEST` at a production or shared Neon database because tests may drop and recreate tables.

## Checks

```bash
uv run pytest
uv run pytest tests/automation -v
uv run ruff check .
uv run pyright
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
npm run test:e2e
```

## Desktop connector app

The customer desktop app lives in `desktop/`. It uses Electron for the native shell and a packaged Python sidecar for the connector runtime. The dashboard stays at `https://schedule.bookinghome.one`, while the connector sidecar pairs and opens WebSockets against the FastAPI backend at `https://api.schedule.bookinghome.one`.

Local unsigned development build:

```bash
uv sync
cd desktop
npm install
npm run typecheck
npm run build
npm run dist:dir
```

Build the Python sidecar for the current platform. The script downloads Chromium into `desktop/resources/ms-playwright` so Electron Builder can ship the browser beside the PyInstaller sidecar:

```bash
./scripts/build-sidecar.sh
```

Build customer artifacts for the current platform:

```bash
./scripts/build-desktop.sh
```

Windows artifacts must be built on Windows because PyInstaller cannot cross-compile the Python sidecar from macOS/Linux to a Windows `.exe`:

```powershell
uv sync --all-groups
cd desktop
npm ci
cd ..
.\scripts\build-desktop.ps1
```

The Windows output is written under `dist/desktop/` and should include an NSIS installer for `Facebook Group Connector`. The same process is automated by `.github/workflows/build-desktop-windows.yml`; run it with GitHub Actions `workflow_dispatch` after adding signing secrets.

Customer builds must be signed. Provide signing credentials through CI/local environment variables or secret stores only:

- macOS: `CSC_LINK`, `CSC_KEY_PASSWORD`, `APPLE_ID`, `APPLE_APP_SPECIFIC_PASSWORD`, `APPLE_TEAM_ID`
- Windows: `WIN_CSC_LINK`, `WIN_CSC_KEY_PASSWORD`
- Auto-update feed: `DESKTOP_UPDATE_FEED_URL`

Do not commit signing certificates, passwords, API keys, or update feed credentials.

## Secrets

Keep real database, service bus, storage, signing, notarization, and update-feed credentials only in environment variables or secret stores. The `.env` file is ignored by git and must not be copied into documentation, source code, tests, or commits.

Rotate any secret that has been pasted into chat, logs, screenshots, issue trackers, or shared terminals.
