# Developer Setup

This project is organized as a monorepo. The current workspace contains architecture contracts and bootstrap tooling; app code will live under `apps/desktop` and `services/inference`.

## Prerequisites

- Node.js 20 or newer
- Python 3.12 or newer
- Rust stable via `rustup`
- ffmpeg on your `PATH`
- Git

## macOS

1. Install tooling:
   ```bash
   brew install node python rustup-init ffmpeg
   rustup-init
   ```
2. Verify your toolchain:
   ```bash
   node -v
   python3 -V
   cargo -V
   rustc -V
   ffmpeg -version
   ```
3. Check the workspace:
   ```bash
   python3 scripts/dev.py doctor
   ```

## Windows

1. Install Node.js from the official installer or `winget`.
2. Install Python 3.12 from python.org or `winget`.
3. Install Rust with `rustup-init.exe`.
4. Install ffmpeg with `winget install Gyan.FFmpeg` or `choco install ffmpeg`.
5. Verify your toolchain in PowerShell:
   ```powershell
   node -v
   python -V
   cargo -V
   rustc -V
   ffmpeg -version
   ```

## Local workflow

- `npm run bootstrap` creates the local data directories used by the MVP.
- `npm run doctor` checks for the expected directories and tools.
- `npm run status` prints the workspace layout and current bootstrap state.
- `npm run bootstrap:models` verifies model placeholder directories and manifests.
- `python3 scripts/dev.py verify` runs the current frontend and backend verification stack when the required tools are installed.

## What You Can Test Now

The current workspace supports layered local verification without packaging the full desktop app yet.

1. Run `npm install`.
2. Run `python3 scripts/dev.py verify`.
3. If you want to inspect the frontend shell, run `npm run dev --workspace @home-voice-studio/desktop`.
4. If you have Rust and the Tauri prerequisites installed, run `npm run tauri:dev --workspace @home-voice-studio/desktop` for the full desktop dev shell.
5. If you want to inspect the Python sidecar directly, run `PYTHONPATH=. python3 -m app.cli --host 127.0.0.1 --port 8765` from `services/inference`.
6. If you want the Playwright smoke scaffold, follow [tests/e2e/README.md](tests/e2e/README.md).

## Current Blocker

- The packaged desktop app is still blocked on the packaged-sidecar work tracked in [docs/remaining-work.md](docs/remaining-work.md).
- That means the browser preview, backend, and a local Tauri dev run can be tested now, but the release-style packaged app is not yet the final test target.

## Repository layout expectations

- `data/profiles` stores local profile metadata and reference clip manifests.
- `data/exports` stores exported audio artifacts.
- `data/cache` stores previews, temp files, and waveform previews.
- `services/inference` owns the FastAPI sidecar and all offline processing orchestration.
- `apps/desktop` owns the desktop shell and user-facing UI.

## Run-time assumptions

- The app should default to safe local storage locations.
- Users must explicitly confirm voice cloning style workflows before profile creation.
- All major features must work from the UI without CLI knowledge.
