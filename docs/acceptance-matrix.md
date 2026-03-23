# Acceptance Matrix

This matrix defines the MVP as testable outcomes. A feature is complete only when the UI flow, backend behavior, and data persistence all work together locally.

## Primary Journeys

| Journey | User Action | Expected Result | Verification |
| --- | --- | --- | --- |
| Speak Text | Enter text, choose a saved voice, set speed, generate speech | A playable audio preview is created and a file can be exported as WAV or MP3 | UI smoke test, API test, export artifact exists |
| Change Voice | Upload a speech file, choose a target profile, set strength and pitch preserve | Converted output is previewable before export | UI smoke test, job status polling, output artifact exists |
| Clean Recording | Upload a noisy recording, choose cleanup mode and level | Cleaned output is previewable and exportable | UI smoke test, pipeline test, output artifact exists |
| Create Profile | Enter profile metadata, attach reference clips, confirm consent | Profile is saved locally and appears in Voice Profiles | Unit test, persistence test, profile list refresh |
| Review History | Open History and inspect prior runs | Prior jobs show status, artifacts, and timestamps | UI smoke test, jobs API test |

## Functional Acceptance Criteria

### Speak Text

- User can enter text in plain language controls without exposing provider internals by default.
- User can select a saved voice profile and adjust `Speed`.
- User can preview generated speech before exporting.
- User can export the result without leaving the current tab.
- Job progress is visible while generation runs.

### Change Voice

- User can upload a local audio file through the UI.
- User can select a saved profile as the target voice.
- User can tune `Strength` and `Pitch Preserve`.
- User can compare before and after previews.
- User can export the converted file locally.

### Clean Recording

- User can choose `Denoise`, `Voice Focus`, or `Vocal Isolation`.
- User can set `Cleanup Level`.
- User can preview the cleaned result before export.
- User can export the cleaned file locally.

### Voice Profiles

- User must explicitly confirm consent before creating a voice-cloning profile.
- User can add at least one reference clip.
- User can reuse the profile in text-to-speech and voice conversion flows.
- Saved profiles persist after app restart.

### History

- User can see recent jobs with status, progress, and timestamps.
- User can reopen artifacts from completed jobs.
- User can identify failed jobs from structured error summaries.

### Settings and Model Manager

- User can view sidecar health and local capability status.
- User can change safe defaults such as output directory and retention days.
- Advanced controls stay hidden until explicitly enabled.

## Non-Functional Acceptance Criteria

- The app runs fully locally with no required network access.
- The app does not write outside approved data folders in normal operation.
- Structured errors distinguish user-safe messages from diagnostic details.
- Cancelled or superseded jobs release temp files.
- Export paths are deterministic and user visible.

## Release Gates

The MVP is releasable only when all of the following are true:

- `Speak Text`, `Change Voice`, and `Clean Recording` each complete end to end.
- Voice profile creation works with consent confirmation and local persistence.
- The sidecar health endpoint reports usable local status.
- Jobs can be created, polled, cancelled, and reopened.
- Export works for both WAV and MP3.

