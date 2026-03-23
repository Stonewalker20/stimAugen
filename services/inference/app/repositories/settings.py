from __future__ import annotations

import json
from pathlib import Path

from app.models.settings import AppSettings


class SettingsRepository:
    def __init__(self, settings_path: Path, default_output_directory: str, inference_host: str) -> None:
        self._settings_path = settings_path
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        self._default_settings = AppSettings(
            defaultOutputDirectory=default_output_directory,
            inferenceHost=inference_host,
        )

    async def get_settings(self) -> AppSettings:
        if not self._settings_path.exists():
            return await self.save_settings(self._default_settings)
        with self._settings_path.open("r", encoding="utf-8") as handle:
            return AppSettings.model_validate(json.load(handle))

    async def save_settings(self, settings: AppSettings) -> AppSettings:
        with self._settings_path.open("w", encoding="utf-8") as handle:
            json.dump(settings.model_dump(mode="json", by_alias=True), handle, indent=2)
        return settings
