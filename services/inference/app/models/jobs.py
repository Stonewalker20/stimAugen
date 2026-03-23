from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.models.common import ApiModel, AudioArtifact, StructuredError


class JobSummary(ApiModel):
    id: str
    kind: str
    status: str
    progress: int
    attempt_count: int = Field(default=0, alias="attemptCount")
    max_attempts: int = Field(default=1, alias="maxAttempts")
    retry_count: int = Field(default=0, alias="retryCount")
    created_at: datetime = Field(alias="createdAt")
    started_at: datetime | None = Field(default=None, alias="startedAt")
    finished_at: datetime | None = Field(default=None, alias="finishedAt")
    cancel_requested_at: datetime | None = Field(default=None, alias="cancelRequestedAt")


class JobResponse(JobSummary):
    request: dict[str, Any]
    result: dict[str, Any] | None = None
    error: StructuredError | None = None
    artifacts: list[AudioArtifact] = []


class JobListResponse(ApiModel):
    jobs: list[JobResponse]


class CancelJobResponse(ApiModel):
    id: str
    status: str
    cancel_requested_at: datetime | None = Field(default=None, alias="cancelRequestedAt")
