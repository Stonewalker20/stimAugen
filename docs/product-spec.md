# Home Voice Studio Product Spec

## Scope

Home Voice Studio is a local-first desktop app for personal home audio work. The MVP covers three user-facing workflows and the supporting management surfaces:

- Speak Text
- Change Voice
- Clean Recording
- Voice Profiles
- History
- Settings
- Model Manager

The application must remain usable without command-line knowledge and without any cloud dependency.

## Repo Layout

The repository is a monorepo with clear boundaries:

```text
apps/desktop/            Tauri v2 + React + TypeScript desktop client
services/inference/      FastAPI sidecar for local processing and persistence
packages/shared-types/   Cross-app TypeScript contracts
packages/ui/             Shared UI components and layout primitives
data/profiles/           Local voice profile records and reference clips
data/exports/            Exported user files
data/cache/              Temporary previews, waveforms, and job artifacts
docs/                    Product, architecture, and implementation notes
scripts/                 Local bootstrap and dev helpers
tests/e2e/               End-to-end coverage for the main journeys
```

## Product Rules

- Use plain-language controls by default: `Voice`, `Speed`, `Strength`, `Pitch Preserve`, and `Cleanup Level`.
- Hide model-specific terminology behind an `Advanced` toggle.
- Require explicit consent before creating or using a voice-cloning profile.
- Keep storage local and safe by default. Never write outside approved app data locations.
- Surface preview playback, progress, and export actions in the same view as the workflow.

## UI Structure

### Primary Tabs

- `Speak Text`: text entry, voice selection, speed control, preview, export
- `Change Voice`: upload input audio, choose target voice profile, tune strength and pitch preserve, preview before and after, export
- `Clean Recording`: upload noisy audio, choose cleanup mode and level, preview, export

### Secondary Views

- `Voice Profiles`: create, edit, activate, and inspect saved voice profiles
- `History`: browse prior jobs, rerun outputs, reopen artifacts
- `Settings`: application behavior, storage, privacy, and defaults
- `Model Manager`: offline model/status management, downloads, and health checks

## Agent Coordination Notes

The work is split into bounded agents so implementation can proceed in parallel.

- Product Architect Agent: docs only, owns the contract and acceptance criteria
- Frontend Agent: `apps/desktop/src/**` and `packages/ui/**`
- Desktop Integration Agent: `apps/desktop/src-tauri/**`
- Backend API Agent: `services/inference/app/api/**` and `services/inference/app/main.py`
- Audio Pipeline Agent: audio load/process/export helpers in `services/inference/app/services/**`
- TTS Agent: provider abstraction and speech generation service
- Voice Conversion Agent: offline conversion workflow and provider abstraction
- Isolation Agent: cleanup workflow and provider abstraction
- Profiles/Data Agent: local persistence, seed data, and repository interfaces
- Jobs/Queue Agent: async execution, polling, retries, cancellation, cleanup
- QA/Test Agent: unit, API, UI smoke, and end-to-end tests
- DevOps/Packaging Agent: bootstrap scripts, developer setup, logging, and packaging

Coordination rules:

- Treat `docs/architecture-contract.md` as the source of truth for shape and boundaries.
- Keep interfaces stable and typed. If a contract changes, update docs before code.
- Do not assume another agent will clean up your artifacts; each agent owns its own files.
- Prefer compatibility shims over broad rewrites when integrating with existing work.

## Delivery Principle

Every major feature must be runnable from the UI:

- Create profile
- Generate speech from text
- Clean uploaded recording
- Convert uploaded speech to a saved voice
- Preview the result
- Export the result

