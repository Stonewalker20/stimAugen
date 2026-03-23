from __future__ import annotations

from app.services.storage import StorageService
from app.utils.privacy import DEFAULT_LOCAL_INFERENCE_HOST, normalize_local_http_url


class SettingsRepository:
    def __init__(self, storage: StorageService) -> None:
        self.storage = storage
        self.path = storage.paths.settings

    def _defaults(self) -> dict[str, object]:
        return {
            "theme": "system",
            "advancedMode": False,
            "defaultExportFormat": "wav",
            "defaultOutputDirectory": str(self.storage.paths.exports),
            "inferenceHost": DEFAULT_LOCAL_INFERENCE_HOST,
            "retentionDays": 14,
            "allowUnsafeVoiceCloning": False,
            "lastSelectedProfileId": None,
        }

    def _sanitize(self, payload: dict[str, object]) -> dict[str, object]:
        sanitized = dict(payload)
        sanitized["inferenceHost"] = normalize_local_http_url(str(sanitized.get("inferenceHost") or ""))
        return sanitized

    def get_settings(self) -> dict[str, object]:
        payload = self.storage.read_json(self.path, self._defaults())
        if not isinstance(payload, dict):
            payload = self._defaults()
        merged = self._sanitize(self._defaults() | payload)
        self.storage.write_json(self.path, merged)
        return merged

    def update_settings(self, patch: dict[str, object]) -> dict[str, object]:
        current = self.get_settings()
        current.update(patch)
        current = self._sanitize(current)
        self.storage.write_json(self.path, current)
        return current
