from __future__ import annotations

from pydantic import Field

from app.models.common import ApiModel


class ProviderCapability(ApiModel):
    id: str
    label: str
    available: bool
    detail: str | None = None


class HealthPaths(ApiModel):
    profiles: str
    exports: str
    cache: str


class HealthResponse(ApiModel):
    status: str
    version: str
    providers: list[ProviderCapability]
    paths: HealthPaths
    uptime_seconds: float = Field(alias="uptimeSeconds")
