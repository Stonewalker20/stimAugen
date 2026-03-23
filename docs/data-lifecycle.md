# Data Lifecycle

## Data Categories

- `profiles`: saved voice profile metadata and reference clips
- `jobs`: queued, running, completed, cancelled, and failed job records
- `cache`: temporary previews, waveform images, chunked intermediates, and transient exports
- `exports`: user-approved output files
- `settings`: application preferences and local environment state

## Storage Rules

- All persistent data stays local.
- Development data lives under the repo `data/` directory.
- Packaged app data lives under the OS app data root.
- Paths must be deterministic so history and export reopening work consistently.

## Canonical Paths

- `data/profiles/{profileId}/`
- `data/cache/jobs/{jobId}/`
- `data/cache/previews/{jobId}/`
- `data/cache/waveforms/{artifactId}/`
- `data/exports/{YYYY}/{MM}/`

## Lifecycle Stages

### 1. Ingest

- User uploads a local file or creates a text request in the UI.
- The frontend passes a typed request to the Rust host.
- The host forwards the request to the Python sidecar.

### 2. Normalize

- Audio is loaded, resampled, and converted to the internal working format.
- Mono normalization, trimming, and loudness adjustment happen before inference.
- The original file remains untouched.

### 3. Process

- The queue creates a job record immediately.
- Work runs asynchronously and emits progress updates.
- Preview jobs use short-lived artifacts, while final export jobs produce durable outputs.

### 4. Persist

- Completed job metadata is written to the local job store.
- Profile updates are saved before the UI reports success.
- Artifacts are written to deterministic paths and registered in the job record.

### 5. Preview and Export

- The UI reads previewable artifacts from the job result.
- Export uses a user-selected destination and final format.
- Exported files are copied or transcoded into the export directory as needed.

### 6. Cleanup

- Temp files from cancelled, failed, or superseded jobs are removed.
- Preview artifacts may be garbage-collected after the retention window.
- Reference clips and profiles are preserved unless the user deletes them.

## Retention Policy

- Keep completed job metadata long enough to support the History view.
- Keep cache data only as long as needed for previews and recovery.
- Allow users to adjust retention days in Settings.
- Never delete exported files without explicit user action.

## Failure Handling

- Failed jobs retain structured error metadata.
- Partial artifacts are cleaned up unless needed for debugging.
- Cancellation is idempotent and leaves the store in a consistent state.

## Recovery Expectations

- The sidecar can restart and rebuild in-memory state from the local store.
- Existing profiles remain available after restart.
- The History view can repopulate from persisted job records.

