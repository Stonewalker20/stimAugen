# Remaining Work

## P0

- Packaged desktop release polish is still incomplete.
  - The repo now produces a launchable macOS `.app` bundle with a staged sidecar.
  - DMG generation, signing, notarization, and Windows installer validation are still open.
  - Owner: Desktop Packaging

- End-to-end desktop usage still needs manual validation.
  - Verification now covers React build, backend tests, `cargo check`, and a successful macOS `.app` package build.
  - Real user-run checks for profile creation, speech generation, cleanup, voice conversion, and export from the packaged app still need to be exercised.
  - Owner: Desktop Integration and QA

## P1

- Model integration is still MVP-grade.
  - TTS uses native or fallback providers.
  - Voice conversion and isolation are DSP-backed placeholders behind stable interfaces.
  - Real local model providers, model selection, and bootstrap flows still need to be implemented.
  - Owner: Model Integration

- Job orchestration still needs deeper runtime behavior.
  - Cancellation is now explicit and persisted, but retries, resume-on-restart, retention enforcement, and stronger cleanup guarantees are still incomplete.
  - Owner: Backend Runtime

- Desktop bridge contracts should become more explicit.
  - The Rust host still leans on generic sidecar route proxying.
  - Release builds should move core flows to typed commands and events for stronger compatibility and error handling.
  - Owner: Desktop Integration and Backend

- Frontend workflow UX still needs more desktop polish.
  - Useful follow-ups include richer job-detail views, cancellation controls, clearer failure recovery, waveform or before-after comparison views, and stronger degraded or offline states.
  - Owner: Frontend

- Test coverage is still narrow.
  - Python API and pipeline tests exist.
  - React unit tests, real Playwright or Tauri E2E runs, and packaging smoke tests are still missing.
  - Owner: QA

## P2

- Release packaging is incomplete.
  - Installers, bundled sidecar assets, platform-specific binary placement, signing, notarization, and release validation remain open.
  - Owner: DevOps and Packaging

- The audio pipeline has a medium-term technical risk.
  - It still depends on `audioop` and `aifc`, which are deprecated and should be replaced before targeting Python 3.13 or newer long term.
  - Owner: Audio Pipeline

- Data lifecycle features are still basic.
  - User-facing deletion flows, export and library management, consent audit metadata, and safer cache pruning policies still need work.
  - Owner: Profiles/Data and Frontend

## Suggested Execution Order

1. Manual packaged-app validation on macOS, then Windows installer validation.
2. Real model-provider integration for TTS, voice conversion, and isolation.
3. Queue, cancellation, and recovery hardening.
4. Playwright or Tauri E2E coverage and release packaging validation.
