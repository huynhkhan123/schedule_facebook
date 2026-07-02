# Windows Unsigned Auto-Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows-first unsigned Electron auto-update pipeline so customers install the desktop connector once and receive future updates through GitHub Releases.

**Architecture:** Use `electron-updater` with GitHub Releases as the update provider. Build unsigned Windows NSIS artifacts in GitHub Actions on `desktop-v*` tags, upload installer/update metadata to the matching GitHub Release, and expose updater state in the desktop UI.

**Tech Stack:** Electron, electron-builder, electron-updater, GitHub Actions, NSIS, TypeScript, React.

## Global Constraints

- Windows is the priority platform for customer testing.
- Windows builds may be unsigned for now; document SmartScreen/unknown publisher warnings.
- Do not require `WIN_CSC_LINK` or `WIN_CSC_KEY_PASSWORD` for test releases.
- Use GitHub Releases as the update feed for the first production-like Windows update path.
- Desktop version in `desktop/package.json` must be bumped before each release tag.

---

### Task 1: Configure unsigned Windows GitHub release publishing

**Files:**
- Modify: `desktop/electron-builder.yml`
- Modify: `.github/workflows/build-desktop-windows.yml`

**Interfaces:**
- Produces GitHub Release assets: `.exe`, `.blockmap`, `latest.yml`.
- Produces tag flow using `desktop-vX.Y.Z`.

Steps:
- [ ] Change `publish` provider to GitHub (`huynhkhan123/schedule_facebook`).
- [ ] Explicitly disable Windows code signing for unsigned test releases.
- [ ] Give workflow `contents: write` permission.
- [ ] Remove required Windows signing secrets from the default workflow env.
- [ ] On tag builds, create/update a GitHub Release and upload Windows artifacts.
- [ ] Keep artifact upload for manual workflow runs.

### Task 2: Improve desktop updater events and UI

**Files:**
- Modify: `desktop/src/main/updater.ts`
- Modify: `desktop/src/preload/index.ts`
- Modify: `desktop/src/renderer/connectorBridge.ts`
- Modify: `desktop/src/renderer/App.tsx`
- Modify: `desktop/src/renderer/styles.css`

**Interfaces:**
- Main process sends updater event objects with `status`, `message`, and optional version/progress.
- Renderer shows current app version, update status, and keeps logs.

Steps:
- [ ] Add typed updater events.
- [ ] Emit checking, available, not-available, downloading, downloaded, and error events.
- [ ] Expose app version through IPC.
- [ ] Render update status in desktop UI.
- [ ] Preserve existing Check for updates button.

### Task 3: Document Windows unsigned release flow

**Files:**
- Modify: `docs/development.md`

**Interfaces:**
- Documents commands for version bump, tag, push, artifact download, and customer warning.

Steps:
- [ ] Add Windows unsigned release section.
- [ ] Include exact tag commands.
- [ ] Explain GitHub Release assets and SmartScreen warning.
- [ ] Explain customer update flow.

### Verification

Run:

```bash
cd desktop
npm run typecheck
npm run build
```

Run:

```bash
bash -n .github/workflows/build-desktop-windows.yml || true
```

YAML syntax is validated by GitHub on push; local shell syntax does not apply to YAML.
