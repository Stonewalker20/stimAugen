# Home Voice Studio Architecture Contract

## Product goals

Home Voice Studio is a local-first desktop application for personal home audio workflows. The MVP must support five complete UI-first journeys:

1. Create and manage a saved voice profile with reference clips and consent metadata.
2. Enter text, choose a voice profile, generate speech, preview it, and export it.
3. Upload a noisy recording, apply cleanup, preview the result, and export it.
4. Upload speech, convert it to a selected saved voice, preview before and after, and export it.
5. Browse job history, review output artifacts, and reopen prior results.

## Product constraints

- Local-first only. No cloud inference, cloud storage, or mandatory online activation.
- Consumer-facing controls by default. Hide model and pipeline internals behind an advanced toggle.
- Safe storage defaults. Write app data only under the local app data root plus the repo `data/` folders in development.
- Explicit confirmation required before voice-cloning style profile creation.
- Every major feature must be usable entirely from the desktop UI.

## Monorepo layout

```text
apps/
  desktop/                 React + TypeScript + Tauri v2 desktop app
packages/
  shared-types/            Shared TS contracts and JSON-shape helpers
  ui/                      Reusable UI primitives and layout components
services/
  inference/               FastAPI sidecar with local audio and model orchestration
data/
  profiles/                Saved voice profiles and reference clips
  exports/                 User exports
  cache/                   Generated previews, temp intermediates, waveforms
docs/
  architecture-contract.md
  developer-setup.md
scripts/
  bootstrap_models.py
  dev.py
tests/
  e2e/
```

## Core domains

### VoiceProfile

- `id`: stable UUID-like string
- `name`: consumer-facing label
- `description`: optional notes
- `consentConfirmed`: boolean
- `createdAt`, `updatedAt`
- `referenceClips`: list of local audio asset references
- `embeddingStatus`: `not_started | processing | ready | error`
- `defaultSettings`: `speed`, `strength`, `pitchPreserve`, `cleanupLevel`
- `analysis`: optional profile summary derived from reference clips

### ProcessingJob

- `id`
- `kind`: `tts | voice_conversion | isolation | waveform | export`
- `status`: `queued | running | completed | failed | cancelled`
- `progress`: 0..100
- `createdAt`, `startedAt`, `finishedAt`
- `request`: typed payload snapshot
- `result`: typed artifact bundle or `null`
- `error`: structured error info or `null`
- `artifacts`: cached file references

### AudioArtifact

- `id`
- `kind`: `input | preview | output | waveform | reference | export`
- `path`
- `format`
- `sampleRate`
- `durationMs`
- `channels`
- `createdAt`

### AppSettings

- `theme`
- `advancedMode`
- `defaultExportFormat`
- `defaultOutputDirectory`
- `inferenceHost`
- `retentionDays`
- `allowUnsafeVoiceCloning`
- `lastSelectedProfileId`

## Frontend information architecture

### Primary tabs

- `Speak Text`
- `Change Voice`
- `Clean Recording`

### Secondary views

- `Voice Profiles`
- `History`
- `Settings`
- `Model Manager`

### UX rules

- Show simple forms and plain-language controls first.
- Keep preview players visible inside each workflow.
- Show job progress inline and in the history center.
- Let users export from result cards without leaving the current tab.
- Use persistent side navigation for secondary views on desktop widths.

## Service boundaries

### React frontend

- Owns view state, optimistic form validation, preview playback, and polling orchestration.
- Talks only to the Rust host bridge.
- Never reads or writes arbitrary filesystem paths directly.

### Tauri/Rust host

- Starts and monitors the Python sidecar.
- Resolves safe app data directories.
- Opens file picker and export dialogs.
- Proxies typed commands between frontend and sidecar.
- Owns desktop packaging metadata and app-level logging.

### Python FastAPI sidecar

- Exposes typed HTTP routes consumed by the Rust layer.
- Coordinates jobs, storage, audio processing, and provider interfaces.
- Persists profiles, settings, job records, and cached outputs locally.
- Runs offline providers for TTS, conversion, isolation, and export.

## HTTP API contract

### `GET /health`

- Returns sidecar state, ffmpeg/provider availability, and data path info.

### `POST /tts`

- Request: text, profile id, speed, preview flag, output format
- Response: accepted job summary with polling URL

### `POST /voice-conversion`

- Request: input artifact, target profile id, strength, pitch preserve, preview flag
- Response: accepted job summary

### `POST /isolation`

- Request: input artifact, cleanup mode, cleanup level, preview flag
- Response: accepted job summary

### `GET /profiles`
- List saved profiles.

### `POST /profiles`
- Create profile with metadata, consent confirmation, and reference clips.

### `PATCH /profiles/{id}`
- Update name, defaults, notes, or consent-related flags.

### `GET /jobs`
- List recent jobs with filters.

### `GET /jobs/{id}`
- Fetch current status and artifacts.

### `POST /jobs/{id}/cancel`
- Cancel a running job.

### `POST /exports`
- Copy or transcode a cached artifact into the export directory.

### `GET /settings`
- Return persisted settings and environment capabilities.

### `PUT /settings`
- Update settings.

## Event flow

1. Frontend collects form data and invokes a Tauri command.
2. Rust validates safe paths, forwards the request to the FastAPI sidecar, and returns an accepted job.
3. Frontend starts polling job status through Rust.
4. Python queue executes the task, writes deterministic artifacts, and updates persisted job state.
5. Completed artifact metadata is returned to the frontend for playback and export.
6. Export uses a Rust dialog to choose destination and a Python export route to finalize format conversion.

## Stable backend interfaces

### TTS provider

- `synthesize(request) -> ProviderArtifact`
- Primary implementation target: OS-native/local engine when available
- Fallback: deterministic tone/narration placeholder marked in metadata

### Voice conversion provider

- `convert(request, profile) -> ProviderArtifact`
- MVP implementation target: offline DSP-based conversion pipeline with stable interface
- Future model-specific engines plug into the same contract

### Isolation provider

- `clean(request) -> ProviderArtifact`
- MVP target: ffmpeg-compatible denoise/focus/isolation chain or Python DSP fallback

### Audio pipeline

- `load`
- `resample`
- `normalize_mono`
- `trim_silence`
- `normalize_loudness`
- `chunk`
- `generate_waveform`
- `export`

## Persistence contract

- Profiles and settings may use JSON in MVP.
- Jobs should use SQLite for reliable polling and recovery if available; otherwise JSONL fallback is acceptable behind a repository interface.
- Cached artifacts use deterministic paths:
  - `data/cache/jobs/{jobId}/`
  - `data/exports/{YYYY}/{MM}/`
  - `data/profiles/{profileId}/`

## Acceptance criteria

### Speak Text

- User can enter text, select a voice, change speed, generate preview audio, and export WAV or MP3.
- Job progress appears in the UI and result history.

### Change Voice

- User can upload audio, choose a saved profile, set strength and pitch preserve, preview the result, and export it.

### Clean Recording

- User can upload audio, choose `Denoise`, `Voice Focus`, or `Vocal Isolation`, tune cleanup level, preview the result, and export it.

### Profiles

- User can create a profile with consent confirmation, attach at least one reference clip, and reuse the profile in TTS and conversion.

### Reliability

- Sidecar health is visible in settings or model manager.
- Failed jobs return structured errors with a user-safe message and diagnostic code.
- Temp files are cleaned after cancellation or superseded preview runs.

## Agent ownership plan

- Product Architect Agent: docs and shared contracts only.
- Frontend Agent: `apps/desktop/src/**`, `packages/ui/**`.
- Desktop Integration Agent: `apps/desktop/src-tauri/**` and frontend bridge files only.
- Backend API Agent: `services/inference/app/api/**`, `services/inference/app/main.py`, API schemas.
- Audio Pipeline Agent: `services/inference/app/services/audio_pipeline.py`, waveform/export helpers.
- TTS Agent: `services/inference/app/services/tts*.py`.
- Voice Conversion Agent: `services/inference/app/services/voice_conversion*.py`.
- Isolation Agent: `services/inference/app/services/isolation*.py`.
- Profiles/Data Agent: repositories, storage, seed data, settings/profile persistence.
- Jobs/Queue Agent: queue runner, cancellation, progress, cleanup.
- QA/Test Agent: tests only.
- DevOps/Packaging Agent: scripts, env setup, packaging docs and configs.

Integration rule: no agent reverts another agent's work; each agent adapts to the shared contract and current workspace state.
