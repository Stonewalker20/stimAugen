from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from app.models.common import ApiModel, AudioArtifact


class ProfileAnalysis(ApiModel):
    estimated_pitch_hz: float | None = Field(default=None, alias="estimatedPitchHz")
    average_level_db: float | None = Field(default=None, alias="averageLevelDb")
    notes: str | None = None


class VoiceDefaults(ApiModel):
    speed: float = 1.0
    strength: float = 0.65
    pitch_preserve: bool = Field(default=True, alias="pitchPreserve")
    cleanup_level: float = Field(default=0.5, alias="cleanupLevel")


class VoiceProfile(ApiModel):
    id: str
    name: str
    description: str | None = None
    consent_confirmed: bool = Field(alias="consentConfirmed")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    embedding_status: str = Field(alias="embeddingStatus")
    reference_clips: list[AudioArtifact] = Field(alias="referenceClips")
    default_settings: VoiceDefaults = Field(alias="defaultSettings")
    analysis: ProfileAnalysis | None = None


class ProfileListResponse(ApiModel):
    profiles: list[VoiceProfile]


class CreateProfileRequest(ApiModel):
    name: str
    description: str | None = None
    consent_confirmed: bool = Field(alias="consentConfirmed")
    reference_clip_paths: list[str] = Field(alias="referenceClipPaths")

    @field_validator("reference_clip_paths")
    @classmethod
    def validate_reference_clips(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("At least one reference clip is required.")
        return value


class UpdateProfileRequest(ApiModel):
    name: str | None = None
    description: str | None = None
    default_settings: VoiceDefaults | None = Field(default=None, alias="defaultSettings")


class ProfileMutationResponse(ApiModel):
    profile: VoiceProfile
