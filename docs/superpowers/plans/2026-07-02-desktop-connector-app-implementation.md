# Desktop Connector App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a signed, auto-updating Electron desktop app that lets customers pair and run the local Facebook connector without source code or terminal commands.

**Architecture:** Keep Python as the connector runtime and extract reusable connector core from the existing CLI. Add a narrow JSON-lines sidecar interface for Electron. Use Electron main/preload/renderer for polished liquid-glass UI, tray/background lifecycle, auto-update, and packaging.

**Tech Stack:** Python 3.12, uv, pytest, PyInstaller, Electron, TypeScript, Vite, React, electron-builder, electron-updater.

## Global Constraints

- Customer server URL defaults to `https://schedule.bookinghome.one`.
- Desktop UI radius is `14px` and follows the web dashboard dark/liquid-glass style.
- Support macOS Apple Silicon, macOS Intel, and Windows x64.
- Tray/background mode is required in v1.
- Auto-update is required in v1.
- macOS code signing and notarization are required for customer builds.
- Windows Authenticode signing is required for customer builds.
- Signing secrets must come from environment variables or secret stores, never repository files.
- No Facebook password storage, cookie/profile upload, CAPTCHA bypass, or arbitrary backend commands.
- Connector jobs remain allowlisted.

---

## Task 1: Python connector core and sidecar JSON interface

**Files:**
- Create: `src/facebook_group_tool/connector/core.py`
- Create: `src/facebook_group_tool/connector/sidecar.py`
- Test: `tests/connector/test_connector_core.py`
- Test: `tests/connector/test_sidecar.py`
- Modify: `src/facebook_group_tool/connector/main.py`
- Modify: `pyproject.toml`

**Deliverable:** CLI keeps working, and Electron can run a packaged sidecar that emits newline-delimited JSON events for pair/run/status.

Steps:
- [ ] Write failing tests for websocket URL, pairing payload, token persistence, and sidecar event formatting.
- [ ] Extract `ConnectorCore` with `pair()` and `run()` async methods.
- [ ] Add `sidecar` command with `pair` and `run` subcommands that emit JSON-lines events without leaking tokens.
- [ ] Keep existing `facebook-group-connector pair/run` CLI compatible.
- [ ] Add PyInstaller as a dev dependency and a `facebook-group-connector-sidecar` script.
- [ ] Run targeted pytest, ruff, and pyright.

## Task 2: Desktop Electron scaffold

**Files:**
- Create: `desktop/package.json`
- Create: `desktop/tsconfig.json`
- Create: `desktop/vite.config.ts`
- Create: `desktop/src/main/main.ts`
- Create: `desktop/src/main/sidecarProcess.ts`
- Create: `desktop/src/main/tray.ts`
- Create: `desktop/src/main/updater.ts`
- Create: `desktop/src/preload/index.ts`
- Create: `desktop/src/renderer/App.tsx`
- Create: `desktop/src/renderer/styles.css`

**Deliverable:** Unsigned dev Electron app can open, pair, start/stop connector, show logs, and hide to tray.

Steps:
- [ ] Add TypeScript Electron/Vite project.
- [ ] Add typed IPC bridge with only `pairConnector`, `startConnector`, `stopConnector`, `checkForUpdates`, and event subscriptions.
- [ ] Add main-process sidecar manager with duplicate-start prevention and clean stop.
- [ ] Add tray menu: Open, Start connector, Stop connector, Check for updates, Quit.
- [ ] Add renderer UI with liquid-glass dark style, 14px radius, status pills, and basic logs.
- [ ] Run desktop typecheck and package smoke test.

## Task 3: Packaging, signing, notarization, and updates

**Files:**
- Create: `desktop/electron-builder.yml`
- Create: `scripts/build-sidecar.sh`
- Create: `scripts/build-desktop.sh`
- Create: `.github/workflows/desktop-release.yml` if GitHub Actions is used
- Modify: `docs/development.md`

**Deliverable:** Release pipeline can build macOS arm64, macOS x64, and Windows x64 artifacts with signed customer builds and update metadata.

Steps:
- [ ] Build sidecar with PyInstaller into platform-specific desktop resources.
- [ ] Configure electron-builder mac dmg/zip artifacts and Windows nsis installer.
- [ ] Configure generic/GitHub update provider without embedding secrets.
- [ ] Wire macOS signing/notarization env vars: `CSC_LINK`, `CSC_KEY_PASSWORD`, `APPLE_ID`, `APPLE_APP_SPECIFIC_PASSWORD`, `APPLE_TEAM_ID`.
- [ ] Wire Windows signing env vars: `WIN_CSC_LINK`, `WIN_CSC_KEY_PASSWORD`.
- [ ] Document local unsigned builds and CI signed release builds in `docs/development.md`.

## Verification

Run before claiming implementation complete:

```bash
uv run pytest tests/connector -v
uv run ruff check .
uv run pyright
cd desktop && npm run typecheck
cd desktop && npm run build
cd desktop && npm run dist:dir
```

Manual smoke checks:

1. Pair desktop app with dashboard code from `https://schedule.bookinghome.one`.
2. Start connector and confirm dashboard shows online.
3. Stop connector and confirm dashboard eventually shows offline.
4. Close window and confirm app remains in tray.
5. Quit from tray and confirm sidecar stops.
6. Build/test equivalent artifacts on macOS Apple Silicon, macOS Intel, and Windows x64.
