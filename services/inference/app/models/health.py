from __future__ import annotations

from pydantic import Field

from app.models.common import ApiModel


class ProviderCapability(ApiModel):
    id: str
    label: str
    available: bool
    detail: str | None = None


class HealthCheck(ApiModel):
    id: str
    label: str
    ok: bool
    detail: str | None = None


class HealthDiagnostics(ApiModel):
    ready: bool
    data_root: str = Field(alias="dataRoot")
    checks: list[HealthCheck]
    warnings: list[str] = Field(default_factory=list)


class HealthPaths(ApiModel):
    profiles: str
    exports: str
    cache: str


class HealthResponse(ApiModel):
    status: str
    version: str
    providers: list[ProviderCapability]
    paths: HealthPaths
    diagnostics: HealthDiagnostics
    uptime_seconds: float = Field(alias="uptimeSeconds")
