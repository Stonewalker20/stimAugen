# Logging and Configuration

The MVP should keep configuration simple and local-only. The following environment variables are reserved for the desktop host and sidecar.

## Environment variables

- `HVS_DATA_ROOT`: overrides the repo-local data root during development
- `HVS_LOG_LEVEL`: sets the global log level, default `info`
- `HVS_LOG_DIR`: overrides the log output directory
- `HVS_INFERENCE_HOST`: sidecar host and port, default `127.0.0.1:8765`
- `HVS_DEFAULT_EXPORT_FORMAT`: default export format, `wav` or `mp3`
- `HVS_ADVANCED_MODE`: enables advanced controls in the UI when set to `true`

## Local paths

- Development logs should live under `data/cache/logs`
- Temporary exports should live under `data/cache/jobs`
- Final user exports should live under `data/exports`

## Logging guidance

- Keep user-facing messages plain language.
- Reserve technical details for structured logs and the advanced UI toggle.
- Attach a stable error code to every failure that reaches the UI.
- Do not log raw reference audio paths or consent-sensitive text unless it is needed for debugging and the user has opted into advanced diagnostics.

## Structured error shape

```json
{
  "code": "tts_provider_unavailable",
  "message": "Speech generation is not available right now.",
  "details": "Optional diagnostics for logs only.",
  "retryable": true
}
```

## Retention

- Keep cache and preview artifacts disposable.
- Clean cancelled or superseded jobs aggressively.
- Retain history only as long as the user setting allows.
