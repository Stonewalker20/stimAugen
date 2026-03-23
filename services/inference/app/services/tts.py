from __future__ import annotations

import math
import platform
import struct
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from shutil import which

from app.api.errors import AppError, NotFoundError
from app.services.audio_pipeline import AudioPipeline
from app.services.jobs import JobManager
from app.services.storage import StorageService
from app.utils.privacy import voice_cloning_allowed
from app.utils.clock import utc_now_iso


@dataclass(frozen=True)
class ProviderResult:
    provider_id: str
    output_path: Path
    warning: str | None = None


class BaseTtsProvider:
    provider_id = "base"

    def available(self) -> bool:
        return False

    def synthesize(self, text: str, destination: Path, speed: float, voice_name: str) -> ProviderResult:
        raise NotImplementedError


class MacSayProvider(BaseTtsProvider):
    provider_id = "macos_say"

    def available(self) -> bool:
        return platform.system() == "Darwin" and which("say") is not None and which("afconvert") is not None

    def synthesize(self, text: str, destination: Path, speed: float, voice_name: str) -> ProviderResult:
        rate = str(max(90, min(360, int(180 * speed))))
        with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as temp:
            temp_path = Path(temp.name)
        try:
            subprocess.run(
                ["say", "-r", rate, "-v", voice_name or "Samantha", "-o", str(temp_path), text],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["afconvert", "-f", "WAVE", "-d", "LEI16@24000", str(temp_path), str(destination)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise AppError("tts_failed", "Native speech synthesis failed.", status_code=500, details=exc.stderr)
        finally:
            temp_path.unlink(missing_ok=True)
        return ProviderResult(self.provider_id, destination)


class WindowsSapiProvider(BaseTtsProvider):
    provider_id = "windows_sapi"

    def available(self) -> bool:
        return platform.system() == "Windows" and which("powershell") is not None

    def synthesize(self, text: str, destination: Path, speed: float, voice_name: str) -> ProviderResult:
        rate = max(-5, min(5, round((speed - 1.0) * 5)))
        script = f"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = {rate}
$synth.SetOutputToWaveFile('{destination}')
$synth.Speak('{text.replace("'", "''")}')
$synth.Dispose()
"""
        try:
            subprocess.run(["powershell", "-Command", script], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            raise AppError("tts_failed", "Windows speech synthesis failed.", status_code=500, details=exc.stderr)
        return ProviderResult(self.provider_id, destination)


class ToneFallbackProvider(BaseTtsProvider):
    provider_id = "tone_fallback"

    def available(self) -> bool:
        return True

    def synthesize(self, text: str, destination: Path, speed: float, voice_name: str) -> ProviderResult:
        destination.parent.mkdir(parents=True, exist_ok=True)
        sample_rate = 24000
        duration_seconds = max(1.5, min(8.0, len(text) / max(speed * 14.0, 1.0)))
        total_frames = int(sample_rate * duration_seconds)
        base_frequency = 190 + (len(voice_name) % 5) * 18
        amplitude = 8200
        frames: list[bytes] = []
        for index in range(total_frames):
            progress = index / sample_rate
            envelope = 0.55 + 0.45 * math.sin(progress * 3.2)
            syllable = 1.0 + 0.25 * math.sin(progress * 9.0)
            tone = math.sin(2 * math.pi * base_frequency * syllable * (index / sample_rate))
            overtone = 0.45 * math.sin(2 * math.pi * (base_frequency * 2.02) * (index / sample_rate))
            sample = int(amplitude * envelope * (tone + overtone) / 1.45)
            frames.append(struct.pack("<h", sample))
        with wave.open(str(destination), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b"".join(frames))
        return ProviderResult(
            self.provider_id,
            destination,
            warning="Using deterministic local fallback audio because no native TTS engine is configured.",
        )


class TtsService:
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
        self.providers = [MacSayProvider(), WindowsSapiProvider(), ToneFallbackProvider()]

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
        return await self.job_manager.submit("tts", payload, self._run_tts)

    def _select_provider(self) -> BaseTtsProvider:
        for provider in self.providers:
            if provider.available():
                return provider
        return ToneFallbackProvider()

    async def _run_tts(self, job_id: str, payload: dict[str, object], update_progress: object) -> dict[str, object]:
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
        await update_progress(20)
        job_dir = self.storage.job_dir(job_id)
        provider = self._select_provider()
        temp_output = self.storage.job_artifact_path(job_id, "tts_native", "wav")
        provider_result = provider.synthesize(
            text=str(payload["text"]),
            destination=temp_output,
            speed=float(payload.get("speed", 1.0)),
            voice_name=str(profile.get("name", "")),
        )
        await update_progress(60)
        prepared = self.audio_pipeline.prepare_input(temp_output, job_dir, stem="tts_prepared")
        output_format = str(payload.get("outputFormat", "wav")).lower()
        final_extension = "mp3" if output_format == "mp3" and self.audio_pipeline.ffmpeg_available else "wav"
        final_output = self.storage.job_artifact_path(job_id, "tts_output", final_extension)
        waveform_path = self.storage.job_waveform_path(job_id, "tts_waveform")
        self.audio_pipeline.export(prepared.path, final_output, fmt=final_extension)
        self.audio_pipeline.generate_waveform(prepared.path, waveform_path)
        await update_progress(90)
        artifact = self.audio_pipeline.inspect_audio(final_output, kind="output", label="Generated Speech", job_id=job_id)
        waveform_artifact = {
            "id": waveform_path.stem,
            "jobId": job_id,
            "kind": "waveform",
            "label": "Speech Waveform",
            "path": str(waveform_path),
            "format": "json",
            "durationMs": prepared.duration_ms,
            "sampleRate": prepared.sample_rate,
            "channels": 1,
            "createdAt": utc_now_iso(),
        }
        return {
            "result": {
                "providerId": provider_result.provider_id,
                "warning": provider_result.warning,
                "profileId": profile_id,
                "outputFormat": final_extension,
            },
            "artifacts": [artifact.model_dump(by_alias=True, mode="json"), waveform_artifact],
        }
