# Packaging Notes

This document covers local release expectations for macOS and Windows. The app is intended to ship as a Tauri v2 desktop application with a Python FastAPI sidecar bundled locally.

## General packaging rules

- Package everything needed for offline use.
- Keep model-specific hooks behind stable interfaces.
- Ship safe defaults for local storage and logging.
- Do not require the user to know about the CLI to use core features.

## Sidecar launch contract

- Development runs may launch the sidecar from the repo with `python -m app.cli`.
- Packaged builds should prefer a bundled `home-voice-studio-inference` executable.
- `HVS_SIDECAR_BIN` may be used as an explicit override for packaged-sidecar discovery during validation.
- The packaged executable should accept `--host`, `--port`, `--log-level`, and `--data-root` so the Rust host can use the same contract in dev and release modes.
- The canonical staging command is `npm run package:sidecar`, and the local macOS app-bundle packaging command is `npm run package:desktop`.

## macOS

- `npm run package:desktop` now produces a launchable `.app` bundle at `apps/desktop/src-tauri/target/release/bundle/macos/Home Voice Studio.app`.
- `npm run verify:desktop` now packages and asserts that the expected current-platform desktop artifact exists.
- Sign the `.app` before distribution.
- Prepare notarization credentials for release builds.
- `npm run package:desktop:dmg` is available for DMG-specific packaging attempts, but notarized/signable DMG distribution is still a release task.
- Include the sidecar executable, model bootstrap metadata, and ffmpeg availability checks.
- Verify that the exported app launches without a developer shell.
- Confirm the bundled sidecar is located under `apps/desktop/src-tauri/binaries/` during the packaging step.

## Windows

- Produce an installer artifact such as MSI or a Tauri-supported package.
- Test launching from the Start menu and from a clean user profile.
- Include ffmpeg and sidecar discovery logic that works without manual PATH edits.
- Verify that file picker and export dialogs use standard Windows locations.
- Confirm the bundled sidecar is located under `apps/desktop/src-tauri/binaries/` during the packaging step.

## Release checklist

1. Confirm `doctor` passes on the target platform.
2. Confirm `npm run verify:desktop` passes on the target platform.
3. Confirm profile creation, TTS, voice conversion, cleanup, and export flows work offline.
4. Confirm logs are written to the expected local directories.
5. Confirm temp files are cleaned after successful and cancelled jobs.
