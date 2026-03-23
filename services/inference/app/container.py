from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING

from .config import AppConfig, load_config

if TYPE_CHECKING:
    from .repositories.profile_repository import ProfileRepository
    from .repositories.settings_repository import SettingsRepository
    from .repositories.job_repository import JobRepository
    from .services.audio_pipeline import AudioPipeline
    from .services.jobs import JobManager
    from .services.isolation import IsolationService
    from .services.storage import StorageService
    from .services.tts import TtsService
    from .services.voice_conversion import VoiceConversionService


@dataclass
class AppContainer:
    config: AppConfig = field(default_factory=load_config)

    @cached_property
    def storage(self) -> "StorageService":
        from .services.storage import StorageService

        return StorageService(self.config.paths)

    @cached_property
    def profile_repository(self) -> "ProfileRepository":
        from .repositories.profile_repository import ProfileRepository

        return ProfileRepository(self.storage)

    @cached_property
    def settings_repository(self) -> "SettingsRepository":
        from .repositories.settings_repository import SettingsRepository

        return SettingsRepository(self.storage)

    @cached_property
    def job_repository(self) -> "JobRepository":
        from .repositories.job_repository import JobRepository

        return JobRepository(self.storage)

    @cached_property
    def audio_pipeline(self) -> "AudioPipeline":
        from .services.audio_pipeline import AudioPipeline

        return AudioPipeline(self.config.paths)

    @cached_property
    def tts_service(self) -> "TtsService":
        from .services.tts import TtsService

        return TtsService(self.audio_pipeline, self.profile_repository, self.settings_repository, self.storage, self.job_manager)

    @cached_property
    def voice_conversion_service(self) -> "VoiceConversionService":
        from .services.voice_conversion import VoiceConversionService

        return VoiceConversionService(
            self.audio_pipeline,
            self.profile_repository,
            self.settings_repository,
            self.storage,
            self.job_manager,
        )

    @cached_property
    def isolation_service(self) -> "IsolationService":
        from .services.isolation import IsolationService

        return IsolationService(self.audio_pipeline, self.storage, self.job_manager)

    @cached_property
    def job_manager(self) -> "JobManager":
        from .services.jobs import JobManager

        return JobManager(self.job_repository, self.storage)
