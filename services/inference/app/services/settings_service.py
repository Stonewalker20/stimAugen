from __future__ import annotations


class SettingsService:
    def __init__(self, settings_repository: object) -> None:
        self.settings_repository = settings_repository

    async def get_settings(self) -> object:
        return self.settings_repository.get_settings()

    async def update_settings(self, request: object) -> object:
        payload = request.model_dump(by_alias=True) if hasattr(request, "model_dump") else dict(request)
        return self.settings_repository.update_settings(payload)
