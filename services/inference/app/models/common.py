from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

PayloadT = TypeVar("PayloadT")


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class StructuredError(ApiModel):
    code: str
    message: str
    details: str | None = None
    retryable: bool = False


class ErrorEnvelope(ApiModel):
    error: StructuredError


class AudioArtifact(ApiModel):
    id: str
    job_id: str | None = Field(default=None, alias="jobId")
    kind: str
    label: str
    path: str
    format: str
    duration_ms: int = Field(alias="durationMs")
    sample_rate: int = Field(alias="sampleRate")
    channels: int
    created_at: datetime = Field(alias="createdAt")


class AcceptedJob(ApiModel):
    job_id: str = Field(alias="jobId")
    kind: str
    status: str
    progress: int
    created_at: datetime = Field(alias="createdAt")
    poll_url: str = Field(alias="pollUrl")


class OkEnvelope(ApiModel, Generic[PayloadT]):
    data: PayloadT
