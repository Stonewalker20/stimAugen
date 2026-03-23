from __future__ import annotations

from pydantic import Field, field_validator

from app.models.common import AcceptedJob, ApiModel


class TtsRequest(ApiModel):
    text: str
    profile_id: str = Field(alias="profileId")
    speed: float = 1.0
    preview: bool = True
    output_format: str = Field(default="wav", alias="outputFormat")

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Text is required.")
        return value


class TtsAcceptedResponse(ApiModel):
    job: AcceptedJob
