# Desktop Connector App Design

## Goal

Build a small desktop application for the local Facebook connector so customers can pair and run the connector without receiving source code, installing Python, or using terminal commands.

The app must support:

- macOS Apple Silicon
- macOS Intel
- Windows x64

## Product Direction

The desktop app should feel consistent with the existing web dashboard while being more polished for customer delivery. It should use a dark, soft, liquid-glass style with rounded 14px surfaces.

Visual direction:

- Dark GitHub-inspired base matching the current dashboard palette.
- Liquid glass cards using translucent surfaces, soft borders, inner highlights, and backdrop-style depth.
- 14px corner radius for primary panels, inputs, and buttons.
- Clear status hierarchy with colored pills for Offline, Pairing, Connecting, Online, and Error.
- Subtle gradient atmosphere using blue/green accents from the dashboard.
- Typography close to the web UI: Inter-style sans text and mono styling for pairing codes/logs.
- Designed hover, focus, disabled, and error states.

Reference tokens from the current web dashboard:

- Background: `#0d1117`
- Surface: `#161b22`
- Elevated: `#1c2128`
- Modal/glass base: `#21262d`
- Border: `#30363d`
- Primary blue: `#2f81f7`
- Success green: `#3fb950`
- Warning yellow: `#d29922`
- Error red: `#f85149`
- Text primary: `#e6edf3`
- Text secondary: `#8b949e`
- Radius: `14px` for the desktop app, intentionally softer than the web dashboard's existing `6px` radius.

## User Experience

The customer opens `Facebook Group Connector` and sees one focused window.

Primary UI:

```text
Facebook Group Connector
Cloud dashboard: https://schedule.bookinghome.one

Pairing code
[ ABC123                           ]
[ Pair connector ]

Status: Offline / Pairing / Connecting / Online / Error
[ Start connector ] [ Stop ]

Activity log
Connected to dashboard...
Waiting for jobs...
```

Behavior:

1. Customer generates a pairing code from the cloud dashboard.
2. Customer opens the desktop app.
3. Customer enters the pairing code.
4. Customer clicks `Pair connector`.
5. App exchanges the pairing code for a connector token and stores it locally.
6. Customer clicks `Start connector`.
7. App connects outbound to `https://schedule.bookinghome.one` over WebSocket.
8. Dashboard can send allowed connector jobs to the local app.
9. App opens the local Playwright browser/profile when a job requires Facebook interaction.
10. App streams basic logs and status updates in the window.

The app should not expose advanced settings in v1. The server URL can default to `https://schedule.bookinghome.one`. If a hidden override is needed for testing, use an environment variable or developer-only config rather than showing it to customers.

## Architecture

Because tray/background mode, auto-update, code signing, and macOS notarization are required from the first customer build, use an Electron desktop shell with a packaged Python connector sidecar instead of a PySide6-only app. Electron gives a mature cross-platform app lifecycle, tray APIs, signed installers, and auto-update support. Python remains the connector runtime so the existing Playwright automation code can be reused.

The app should be split into four layers:

### Connector Core

Reusable async connector logic shared by CLI and desktop app sidecar.

Responsibilities:

- Pair connector with backend.
- Save/load connector token and config.
- Open WebSocket connection.
- Send hello/presence events.
- Receive job notifications.
- Fetch allowed jobs.
- Run job via the existing connector job runner.
- Send progress, completion, and failure events.

This layer must not depend on Electron, Node, or any desktop UI framework.

### Python Connector Sidecar

A packaged Python executable embedded inside the desktop app bundle.

Responsibilities:

- Expose a narrow local process interface for the Electron shell.
- Support `pair`, `run`, and `stop` style commands.
- Emit newline-delimited JSON events to stdout for status/log updates.
- Never accept arbitrary shell commands from the Electron UI or backend.

### Electron Desktop Shell

Native desktop wrapper and customer-facing UI.

Responsibilities:

- Render the pairing form.
- Render Start/Stop controls.
- Render status pill.
- Render activity log.
- Manage the Python connector sidecar process.
- Disable buttons during invalid states.
- Show clear error text.
- Provide tray/background behavior.
- Integrate auto-update checks.

The UI must not implement backend protocol or Facebook job handling directly.

### App Lifecycle Services

Electron main-process services for production behavior.

Responsibilities:

- Single-instance lock so duplicate connector loops do not run.
- Tray menu: Open, Start connector, Stop connector, Quit.
- Background mode: closing the window hides to tray instead of quitting.
- Optional launch-at-login preference after pairing.
- Auto-update check/download/install using a signed update feed.
- Crash-safe cleanup of the Python sidecar on quit.

## Security and Safety

The app must preserve the existing connector safety model:

- No Facebook password storage.
- No upload of cookies or browser profiles to Azure.
- No CAPTCHA/checkpoint bypass.
- No arbitrary command execution from backend.
- Only allowlisted job types are accepted.
- Connector token is stored locally under the user's app config directory.
- Logs shown in the UI should avoid secrets and full tokens.

## Packaging, Signing, and Auto-Update

Use PyInstaller only for the embedded Python connector sidecar. Use Electron Builder for the customer-facing desktop app, installers, signing, notarization, and update artifacts.

Outputs:

```text
dist/desktop/macos-arm64/Facebook Group Connector.dmg
dist/desktop/macos-x64/Facebook Group Connector.dmg
dist/desktop/windows-x64/Facebook Group Connector Setup.exe
```

Build constraints:

- Build macOS Apple Silicon on Apple Silicon hardware.
- Build macOS Intel on Intel macOS hardware or a dedicated compatible runner.
- Build Windows x64 on Windows.
- PyInstaller should be treated as a Python dev/build dependency, not a runtime dependency for the backend service.
- Electron Builder should be treated as a frontend desktop build dependency.

Signing requirements:

- macOS builds must be signed with an Apple Developer ID Application certificate.
- macOS `.dmg` artifacts must be notarized with Apple before sending to customers.
- Windows installers must be Authenticode signed with a code-signing certificate.
- Signing credentials must come from CI/local environment variables or secret stores, never from repository files.
- Unsigned local development builds may exist, but customer builds must be signed.

Auto-update requirements:

- Use Electron auto-update through `electron-updater` and signed Electron Builder artifacts.
- Host update artifacts on a controlled release channel, such as GitHub Releases, Azure Blob Storage static hosting, or another HTTPS endpoint owned by the operator.
- App checks for updates on startup and from the tray menu.
- App downloads updates in the background and prompts the user to restart/install.
- Updates must preserve local connector config and browser profile paths.
- Failed update checks must not prevent the connector from running.
- The update feed URL must be configurable per release channel without exposing secrets in the app.

Tray/background requirements:

- The app must create a system tray/menu bar item on startup.
- Closing the main window hides it to tray instead of quitting.
- Tray menu must include: Open, Start connector, Stop connector, Check for updates, Quit.
- Quit must stop the connector sidecar cleanly before exiting.
- The app must prevent multiple running instances.

## Playwright Browser Runtime

For v1, do not bundle Chromium into the app package.

Instead:

1. On first start, check whether the Playwright browser runtime exists.
2. If missing, show a customer-friendly message in the log: `Installing browser runtime. This may take a few minutes...`.
3. Run Playwright browser install for Chromium.
4. Continue once installed.

This keeps the first app package smaller and reduces packaging complexity. A later installer version can bundle browsers if offline install becomes a requirement.

## Error Handling

The app should handle these states explicitly:

- Invalid pairing code.
- Expired pairing code.
- Server unavailable.
- WebSocket disconnected.
- Connector token missing.
- Playwright browser runtime missing or install failed.
- Job runner error.
- User stops the connector.

Error messages should be customer-friendly and should include enough detail for support without exposing secrets.

## Testing Strategy

Automated tests should cover connector core behavior without requiring the desktop UI to run visually:

- Pairing request builds the expected payload.
- Config/token is saved and loaded correctly.
- WebSocket URL uses `wss://` for HTTPS servers.
- Worker state transitions prevent duplicate starts.
- Desktop module imports without starting the app.

Manual verification should cover:

1. Build app on macOS Apple Silicon.
2. Open app.
3. Pair with dashboard code.
4. Start connector.
5. Dashboard shows connector online.
6. Stop connector.
7. Dashboard eventually shows connector offline.
8. Repeat equivalent packaging smoke test on macOS Intel and Windows.

## Non-Goals for v1

Do not include these in the first desktop app implementation:

- Advanced settings page.
- Bundled Chromium runtime.
- Local dashboard replacement.
- Complex multi-account connector management.
- Silent forced updates with no user prompt.

Tray/background mode, auto-update, code signing, and macOS notarization are v1 requirements because the app will be distributed directly to customers and should be maintainable without repeatedly sending manual replacement files.
