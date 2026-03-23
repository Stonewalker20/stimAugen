# Local Testing

This is the shortest path to verifying the current workspace on macOS or Windows.

## What Works Now

- Frontend compile and production build
- Python sidecar tests and import/runtime checks
- Workspace bootstrap and model placeholder bootstrap
- Playwright smoke scaffolding for the main journeys
- Packaged-sidecar staging entrypoint via `npm run package:sidecar`
- Packaged macOS `.app` bundle via `npm run package:desktop`

## One Command

```bash
python3 scripts/dev.py verify
```

That command:

1. Creates the local data folders.
2. Prints the current toolchain and workspace status.
3. Ensures the local model manifest placeholder exists.
4. Runs frontend typecheck and build.
5. Runs the Python backend test suite.
6. Runs Python bytecode compilation for the backend tree.
7. Runs a Rust desktop `cargo check` when `cargo` is installed.

## Manual Workflow

Use these commands when you want to inspect each layer separately.

```bash
npm install
python3 scripts/dev.py bootstrap
python3 scripts/dev.py bootstrap:models
python3 scripts/dev.py doctor
npm run typecheck
npm run build
PYTHONPATH=services/inference python3 -m pytest services/inference/tests -q
python3 -m compileall services/inference/app services/inference/tests
```

## Desktop Preview

If you want to inspect the current frontend shell in a browser preview:

```bash
npm run dev --workspace @home-voice-studio/desktop
```

That only exercises the React side. It does not prove packaged desktop startup.

## Desktop Dev Run

If you have Rust and the Tauri prerequisites installed, you can run the full desktop shell in development mode:

```bash
npm run tauri:dev --workspace @home-voice-studio/desktop
```

In development, the Rust host falls back to the repo-local Python sidecar launcher automatically.

## Packaged Launcher Path

If you have installed the packaging extra for the Python sidecar, you can stage the bundled desktop artifact with:

```bash
npm run package:desktop
```

That command will either copy a prebuilt `HVS_SIDECAR_BIN` into the Tauri bundle area or attempt a PyInstaller build from `services/inference`.
On macOS it currently finishes with a launchable `.app` bundle at `apps/desktop/src-tauri/target/release/bundle/macos/Home Voice Studio.app`.

## Privacy Defaults

- The sidecar host is locked to loopback-only addresses. Remote `inferenceHost` values are ignored.
- Voice profile creation and voice generation require explicit consent by default.
- If `allowUnsafeVoiceCloning` is enabled in Settings, the app will allow consent overrides locally, but that setting stays on the current machine only.

## Sidecar Preview

If you want to run the Python sidecar directly:

```bash
cd services/inference
PYTHONPATH=. python3 -m app.cli --host 127.0.0.1 --port 8765
```

The health endpoint should respond at `http://127.0.0.1:8765/health`.

## Playwright Smoke

Run the E2E smoke suite only after the UI preview is already running:

```bash
HVS_E2E_RUN=1 HVS_E2E_URL=http://127.0.0.1:1420 npx playwright test --config tests/e2e/playwright.config.ts
```

## When You Can Test Run

- You can test the frontend and backend layers now with `python3 scripts/dev.py verify`.
- You can test the browser preview now with `npm run dev --workspace @home-voice-studio/desktop`.
- You can test the full desktop dev run now with `npm run tauri:dev --workspace @home-voice-studio/desktop` once Rust is installed on your machine.
- You can test the packaged macOS launcher now with `npm run package:desktop`.
- The remaining packaging gap is release-grade distribution polish such as DMG/notarization and Windows installer validation.
