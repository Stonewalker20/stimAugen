from __future__ import annotations

from pydantic import Field

from app.models.common import AcceptedJob, ApiModel


class VoiceConversionRequest(ApiModel):
    input_path: str = Field(alias="inputPath")
    profile_id: str = Field(alias="profileId")
    strength: float = 0.65
    pitch_preserve: bool = Field(default=True, alias="pitchPreserve")
    preview: bool = True
    output_format: str = Field(default="wav", alias="outputFormat")


class VoiceConversionAcceptedResponse(ApiModel):
    job: AcceptedJob
