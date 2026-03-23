from __future__ import annotations

from dataclasses import dataclass

from app.api.deps import ServiceContainer
from app.config import load_config
from app.repositories import JobRepository, ProfileRepository, SettingsRepository
from app.services.audio_pipeline import AudioPipeline
from app.services.export_service import ExportService
from app.services.health_service import HealthService
from app.services.isolation import IsolationService
from app.services.jobs import JobManager, JobService
from app.services.profile_service import ProfileService
from app.services.settings_service import SettingsService
from app.services.storage import StorageService
from app.services.tts import TtsService
from app.services.voice_conversion import VoiceConversionService


@dataclass(slots=True)
class RuntimeServiceContainer(ServiceContainer):
    _job_manager: JobManager

    async def shutdown(self) -> None:
        await self._job_manager.shutdown()


async def build_service_container() -> RuntimeServiceContainer:
    config = load_config()
    storage = StorageService(config.paths)
    profile_repository = ProfileRepository(storage)
    settings_repository = SettingsRepository(storage)
    job_repository = JobRepository(storage)
    audio_pipeline = AudioPipeline()
    job_manager = JobManager(job_repository, storage)

    return RuntimeServiceContainer(
        health_service=HealthService(config),
        tts_service=TtsService(audio_pipeline, profile_repository, storage, job_manager),
        voice_conversion_service=VoiceConversionService(audio_pipeline, profile_repository, storage, job_manager),
        isolation_service=IsolationService(audio_pipeline, storage, job_manager),
        profile_service=ProfileService(profile_repository),
        job_service=JobService(job_manager),
        export_service=ExportService(audio_pipeline, storage),
        settings_service=SettingsService(settings_repository),
        _job_manager=job_manager,
    )
