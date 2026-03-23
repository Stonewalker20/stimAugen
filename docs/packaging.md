# Packaging Notes

This document covers local release expectations for macOS and Windows. The app is intended to ship as a Tauri v2 desktop application with a Python FastAPI sidecar bundled locally.

## General packaging rules

- Package everything needed for offline use.
- Keep model-specific hooks behind stable interfaces.
- Ship safe defaults for local storage and logging.
- Do not require the user to know about the CLI to use core features.

## macOS

- Build an app bundle and sign it before distribution.
- Prepare notarization credentials for release builds.
- Include the Python sidecar, model bootstrap metadata, and ffmpeg availability checks.
- Verify that the exported app launches without a developer shell.

## Windows

- Produce an installer artifact such as MSI or a Tauri-supported package.
- Test launching from the Start menu and from a clean user profile.
- Include ffmpeg and sidecar discovery logic that works without manual PATH edits.
- Verify that file picker and export dialogs use standard Windows locations.

## Release checklist

1. Confirm `doctor` passes on the target platform.
2. Confirm the UI launches with a bundled sidecar.
3. Confirm profile creation, TTS, voice conversion, cleanup, and export flows work offline.
4. Confirm logs are written to the expected local directories.
5. Confirm temp files are cleaned after successful and cancelled jobs.
