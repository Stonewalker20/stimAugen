from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from app.api.errors import AppError
from app.config import AppPaths
from app.models.tts import TtsRequest
from app.models.voice_conversion import VoiceConversionRequest
from app.repositories.job_repository import JobRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.settings_repository import SettingsRepository
from app.services.audio_pipeline import AudioPipeline
from app.services.jobs import JobManager
from app.services.storage import StorageService
from app.services.tts import TtsService
from app.services.voice_conversion import VoiceConversionService


def _build_services(tmp_path: Path):
    paths = AppPaths.create(tmp_path)
    storage = StorageService(paths)
    settings_repository = SettingsRepository(storage)
    profile_repository = ProfileRepository(storage)
    job_repository = JobRepository(storage)
    audio_pipeline = AudioPipeline()
    job_manager = JobManager(job_repository, storage)
    tts_service = TtsService(audio_pipeline, profile_repository, settings_repository, storage, job_manager)
    voice_conversion_service = VoiceConversionService(
        audio_pipeline,
        profile_repository,
        settings_repository,
        storage,
        job_manager,
    )
    return storage, settings_repository, profile_repository, tts_service, voice_conversion_service


def test_settings_repository_forces_local_inference_host(tmp_path: Path) -> None:
    _, settings_repository, _, _, _ = _build_services(tmp_path)

    saved = settings_repository.update_settings({"inferenceHost": "https://example.com:9000"})

    assert saved["inferenceHost"] == "http://127.0.0.1:8765"
    assert settings_repository.get_settings()["inferenceHost"] == "http://127.0.0.1:8765"


def test_voice_generation_blocks_unconsented_profiles(tmp_path: Path) -> None:
    storage, _, _, tts_service, voice_conversion_service = _build_services(tmp_path)
    profile_id = "profile_blocked"
    storage.write_json(
        storage.profile_manifest(profile_id),
        {
            "id": profile_id,
            "name": "Blocked Voice",
            "description": "Missing consent.",
            "consentConfirmed": False,
            "createdAt": "2026-03-23T00:00:00+00:00",
            "updatedAt": "2026-03-23T00:00:00+00:00",
            "embeddingStatus": "ready",
            "referenceClips": [],
            "defaultSettings": {
                "speed": 1.0,
                "strength": 0.65,
                "pitchPreserve": True,
                "cleanupLevel": 0.5,
            },
            "analysis": None,
        },
    )

    with pytest.raises(AppError) as exc_info:
        asyncio.run(
            tts_service.submit(
                TtsRequest(
                    text="Hello",
                    profile_id=profile_id,
                    preview=True,
                    output_format="wav",
                )
            )
        )
    assert exc_info.value.error.code == "consent_required"
    assert exc_info.value.status_code == 422

    with pytest.raises(AppError) as exc_info:
        asyncio.run(
            voice_conversion_service.submit(
                VoiceConversionRequest(
                    input_path=str(tmp_path / "input.wav"),
                    profile_id=profile_id,
                    preview=True,
                    output_format="wav",
                )
            )
        )
    assert exc_info.value.error.code == "consent_required"
    assert exc_info.value.status_code == 422
