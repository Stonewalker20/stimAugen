from __future__ import annotations

from pydantic import Field

from app.models.common import ApiModel, AudioArtifact


class ExportRequest(ApiModel):
    artifact_path: str = Field(alias="artifactPath")
    destination_path: str = Field(alias="destinationPath")
    format: str


class ExportResponse(ApiModel):
    artifact: AudioArtifact
