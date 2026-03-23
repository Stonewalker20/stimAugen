from __future__ import annotations

from pathlib import Path

from app.services.storage import StorageService


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
            "inferenceHost": "http://127.0.0.1:8765",
            "retentionDays": 14,
            "allowUnsafeVoiceCloning": False,
            "lastSelectedProfileId": None,
        }

    def get_settings(self) -> dict[str, object]:
        payload = self.storage.read_json(self.path, self._defaults())
        if not isinstance(payload, dict):
            payload = self._defaults()
        merged = self._defaults() | payload
        self.storage.write_json(self.path, merged)
        return merged

    def update_settings(self, patch: dict[str, object]) -> dict[str, object]:
        current = self.get_settings()
        current.update(patch)
        self.storage.write_json(self.path, current)
        return current
