from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from fastapi import Request


@runtime_checkable
class HealthService(Protocol):
    async def get_health(self) -> object: ...


@runtime_checkable
class TtsService(Protocol):
    async def submit(self, request: object) -> object: ...


@runtime_checkable
class VoiceConversionService(Protocol):
    async def submit(self, request: object) -> object: ...


@runtime_checkable
class IsolationService(Protocol):
    async def submit(self, request: object) -> object: ...


@runtime_checkable
class ProfileService(Protocol):
    async def list_profiles(self) -> object: ...

    async def create_profile(self, request: object) -> object: ...

    async def update_profile(self, profile_id: str, request: object) -> object: ...


@runtime_checkable
class JobService(Protocol):
    async def list_jobs(self, kind: str | None = None, status: str | None = None, limit: int = 50) -> object: ...

    async def get_job(self, job_id: str) -> object: ...

    async def cancel_job(self, job_id: str) -> object: ...


@runtime_checkable
class ExportService(Protocol):
    async def export_artifact(self, request: object) -> object: ...


@runtime_checkable
class SettingsService(Protocol):
    async def get_settings(self) -> object: ...

    async def update_settings(self, request: object) -> object: ...


@dataclass(slots=True)
class ServiceContainer:
    health_service: HealthService
    tts_service: TtsService
    voice_conversion_service: VoiceConversionService
    isolation_service: IsolationService
    profile_service: ProfileService
    job_service: JobService
    export_service: ExportService
    settings_service: SettingsService


def get_services(request: Request) -> ServiceContainer:
    return request.app.state.services  # type: ignore[return-value]
