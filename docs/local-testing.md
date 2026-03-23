# Local Testing

This is the shortest path to verifying the current workspace on macOS or Windows.

## What Works Now

- Frontend compile and production build
- Python sidecar tests and import/runtime checks
- Workspace bootstrap and model placeholder bootstrap
- Playwright smoke scaffolding for the main journeys

The full packaged Tauri desktop app is still blocked on the remaining packaged-sidecar work. You can still verify the frontend and backend layers locally now.

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
- You cannot yet treat the packaged desktop app as done until the packaged-sidecar and packaging tasks in `docs/remaining-work.md` are closed.
