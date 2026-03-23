from __future__ import annotations

from pathlib import Path

from app.api.errors import AppError, NotFoundError
from app.services.audio_pipeline import AudioPipeline
from app.services.jobs import JobManager
from app.services.storage import StorageService
from app.utils.privacy import voice_cloning_allowed
from app.utils.clock import utc_now_iso


def _clamp(value: float) -> int:
    return max(-32768, min(32767, int(value)))


def _smooth(samples: list[int], amount: float) -> list[int]:
    if len(samples) < 3:
        return samples
    output = list(samples)
    blend = max(0.0, min(1.0, amount))
    for index in range(1, len(samples) - 1):
        averaged = int((samples[index - 1] + samples[index] + samples[index + 1]) / 3)
        output[index] = int(samples[index] * (1 - blend) + averaged * blend)
    return output


def _brighten(samples: list[int], amount: float) -> list[int]:
    output: list[int] = []
    last = 0
    blend = max(0.0, min(0.8, amount))
    for value in samples:
        emphasized = int(value + (value - last) * blend)
        output.append(_clamp(emphasized))
        last = value
    return output


def _resample_samples(samples: list[int], factor: float) -> list[int]:
    factor = max(0.85, min(1.15, factor))
    target_length = max(1, int(len(samples) / factor))
    resampled: list[int] = []
    for index in range(target_length):
        source_index = index * factor
        left = int(source_index)
        right = min(left + 1, len(samples) - 1)
        mix = source_index - left
        value = samples[left] * (1 - mix) + samples[right] * mix
        resampled.append(_clamp(value))
    return resampled


class VoiceConversionService:
    def __init__(
        self,
        audio_pipeline: AudioPipeline,
        profile_repository: object,
        settings_repository: object,
        storage: StorageService,
        job_manager: JobManager,
    ) -> None:
        self.audio_pipeline = audio_pipeline
        self.profile_repository = profile_repository
        self.settings_repository = settings_repository
        self.storage = storage
        self.job_manager = job_manager

    async def submit(self, request: object) -> object:
        payload = request.model_dump(by_alias=True) if hasattr(request, "model_dump") else dict(request)
        profile_id = str(payload["profileId"])
        profile = self.profile_repository.get_profile(profile_id)
        if profile is None:
            raise NotFoundError("profile", profile_id)
        settings = self.settings_repository.get_settings()
        if not voice_cloning_allowed(profile, settings):
            raise AppError(
                "consent_required",
                "Voice cloning is blocked until the selected profile has explicit consent.",
                status_code=422,
            )
        return await self.job_manager.submit("voice_conversion", payload, self._run_conversion)

    async def _run_conversion(self, job_id: str, payload: dict[str, object], update_progress: object) -> dict[str, object]:
        profile = self.profile_repository.get_profile(str(payload["profileId"]))
        if profile is None:
            raise NotFoundError("profile", str(payload["profileId"]))
        settings = self.settings_repository.get_settings()
        if not voice_cloning_allowed(profile, settings):
            raise AppError(
                "consent_required",
                "Voice cloning is blocked until the selected profile has explicit consent.",
                status_code=422,
            )
        input_path = Path(str(payload["inputPath"]))
        if not input_path.exists():
            raise AppError("missing_input", "The source audio file could not be found.", status_code=404, details=str(input_path))
        await update_progress(20)
        job_dir = self.storage.job_dir(job_id)
        prepared = self.audio_pipeline.prepare_input(input_path, job_dir, stem="voice_conversion_input")
        strength = float(payload.get("strength", 0.65))
        pitch_preserve = bool(payload.get("pitchPreserve", True))
        target_pitch = float(((profile.get("analysis") or {}).get("estimatedPitchHz")) or 180.0)
        target_level = float(((profile.get("analysis") or {}).get("averageLevelDb")) or -18.0)

        def transform(samples: list[int], rate: int) -> list[int]:
            processed = _smooth(samples, amount=0.35 * strength) if target_pitch < 170 else _brighten(samples, amount=0.45 * strength)
            gain_ratio = 10 ** ((target_level - (-16.0)) / 20.0)
            processed = [_clamp(sample * (1.0 + (gain_ratio - 1.0) * strength)) for sample in processed]
            if not pitch_preserve:
                factor = 1.0 + ((target_pitch - 180.0) / 360.0) * strength
                processed = _resample_samples(processed, factor)
            return processed

        transformed_wav = self.storage.job_artifact_path(job_id, "voice_conversion_processed", "wav")
        self.audio_pipeline.transform_samples(prepared.path, transformed_wav, transform)
        await update_progress(70)
        output_format = str(payload.get("outputFormat", "wav")).lower()
        final_extension = "mp3" if output_format == "mp3" and self.audio_pipeline.ffmpeg_available else "wav"
        final_output = self.storage.job_artifact_path(job_id, "voice_conversion_output", final_extension)
        waveform_path = self.storage.job_waveform_path(job_id, "voice_conversion_waveform")
        self.audio_pipeline.export(transformed_wav, final_output, fmt=final_extension)
        self.audio_pipeline.generate_waveform(transformed_wav, waveform_path)
        artifact = self.audio_pipeline.inspect_audio(final_output, kind="output", label="Converted Voice", job_id=job_id)
        await update_progress(90)
        return {
            "result": {
                "mode": "dsp_fallback",
                "profileId": payload["profileId"],
                "strength": strength,
                "pitchPreserve": pitch_preserve,
            },
            "artifacts": [
                artifact.model_dump(by_alias=True, mode="json"),
                {
                    "id": waveform_path.stem,
                    "jobId": job_id,
                    "kind": "waveform",
                    "label": "Converted Waveform",
                    "path": str(waveform_path),
                    "format": "json",
                    "durationMs": artifact.duration_ms,
                    "sampleRate": artifact.sample_rate,
                    "channels": 1,
                    "createdAt": utc_now_iso(),
                },
            ],
        }
