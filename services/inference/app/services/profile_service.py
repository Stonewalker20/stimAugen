from __future__ import annotations

from app.api.errors import AppError, NotFoundError


class ProfileService:
    def __init__(self, profile_repository: object) -> None:
        self.profile_repository = profile_repository

    async def list_profiles(self) -> object:
        return self.profile_repository.list_profiles()

    async def create_profile(self, request: object) -> object:
        payload = request.model_dump(by_alias=True) if hasattr(request, "model_dump") else dict(request)
        if not payload.get("consentConfirmed"):
            raise AppError(
                code="consent_required",
                message="Consent must be confirmed before creating a voice profile.",
                status_code=422,
            )
        return self.profile_repository.create_profile(payload)

    async def update_profile(self, profile_id: str, request: object) -> object:
        payload = request.model_dump(by_alias=True, exclude_none=True) if hasattr(request, "model_dump") else dict(request)
        updated = self.profile_repository.update_profile(profile_id, payload)
        if updated is None:
            raise NotFoundError("profile", profile_id)
        return updated
