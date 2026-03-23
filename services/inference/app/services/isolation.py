from __future__ import annotations

from pathlib import Path

from app.api.errors import AppError
from app.services.audio_pipeline import AudioPipeline
from app.services.jobs import JobManager
from app.services.storage import StorageService
from app.utils.clock import utc_now_iso


def _clamp(value: float) -> int:
    return max(-32768, min(32767, int(value)))


def _gate(samples: list[int], threshold: int) -> list[int]:
    output: list[int] = []
    for value in samples:
        output.append(0 if abs(value) < threshold else value)
    return output


def _focus(samples: list[int], blend: float) -> list[int]:
    output: list[int] = []
    last = 0
    for value in samples:
        focused = int(value + (value - last) * blend)
        output.append(_clamp(focused))
        last = value
    return output


class IsolationService:
    def __init__(
        self,
        audio_pipeline: AudioPipeline,
        storage: StorageService,
        job_manager: JobManager,
    ) -> None:
        self.audio_pipeline = audio_pipeline
        self.storage = storage
        self.job_manager = job_manager

    async def submit(self, request: object) -> object:
        payload = request.model_dump(by_alias=True) if hasattr(request, "model_dump") else dict(request)
        return await self.job_manager.submit("isolation", payload, self._run_isolation)

    async def _run_isolation(self, job_id: str, payload: dict[str, object], update_progress: object) -> dict[str, object]:
        input_path = Path(str(payload["inputPath"]))
        if not input_path.exists():
            raise AppError("missing_input", "The source audio file could not be found.", status_code=404, details=str(input_path))
        await update_progress(20)
        job_dir = self.storage.job_dir(job_id)
        prepared = self.audio_pipeline.prepare_input(input_path, job_dir, stem="isolation_input")
        level = max(0.1, min(1.0, float(payload.get("cleanupLevel", 0.5))))
        threshold = int(400 + level * 1800)
        mode = str(payload.get("mode", "denoise"))

        def transform(samples: list[int], rate: int) -> list[int]:
            gated = _gate(samples, threshold)
            if mode == "voice_focus":
                return _focus(gated, blend=0.28 + level * 0.2)
            if mode == "vocal_isolation":
                return _focus(gated, blend=0.42 + level * 0.25)
            return gated

        cleaned_wav = self.storage.job_artifact_path(job_id, "isolation_processed", "wav")
        self.audio_pipeline.transform_samples(prepared.path, cleaned_wav, transform)
        await update_progress(70)
        output_format = str(payload.get("outputFormat", "wav")).lower()
        final_extension = "mp3" if output_format == "mp3" and self.audio_pipeline.ffmpeg_available else "wav"
        final_output = self.storage.job_artifact_path(job_id, "isolation_output", final_extension)
        self.audio_pipeline.export(cleaned_wav, final_output, fmt=final_extension)
        waveform_path = self.storage.job_waveform_path(job_id, "isolation_waveform")
        self.audio_pipeline.generate_waveform(cleaned_wav, waveform_path)
        artifact = self.audio_pipeline.inspect_audio(final_output, kind="output", label="Cleaned Audio", job_id=job_id)
        await update_progress(90)
        return {
            "result": {
                "mode": mode,
                "cleanupLevel": level,
                "providerId": "dsp_cleanup",
            },
            "artifacts": [
                artifact.model_dump(by_alias=True, mode="json"),
                {
                    "id": waveform_path.stem,
                    "jobId": job_id,
                    "kind": "waveform",
                    "label": "Cleanup Waveform",
                    "path": str(waveform_path),
                    "format": "json",
                    "durationMs": artifact.duration_ms,
                    "sampleRate": artifact.sample_rate,
                    "channels": 1,
                    "createdAt": utc_now_iso(),
                },
            ],
        }
