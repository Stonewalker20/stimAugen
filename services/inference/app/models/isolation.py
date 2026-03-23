from __future__ import annotations

from pydantic import Field

from app.models.common import AcceptedJob, ApiModel


class IsolationRequest(ApiModel):
    input_path: str = Field(alias="inputPath")
    mode: str
    cleanup_level: float = Field(default=0.5, alias="cleanupLevel")
    preview: bool = True
    output_format: str = Field(default="wav", alias="outputFormat")


class IsolationAcceptedResponse(ApiModel):
    job: AcceptedJob
