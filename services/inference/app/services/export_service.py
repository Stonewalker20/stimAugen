from __future__ import annotations

from pathlib import Path

from app.api.errors import AppError
from app.utils.clock import utc_now_iso
from app.utils.ids import make_id


class ExportService:
    def __init__(self, audio_pipeline: object, storage: object) -> None:
        self.audio_pipeline = audio_pipeline
        self.storage = storage

    async def export_artifact(self, request: object) -> object:
        payload = request.model_dump(by_alias=True) if hasattr(request, "model_dump") else dict(request)
        source = Path(payload["artifactPath"])
        if not source.exists():
            raise AppError(
                code="artifact_missing",
                message="The selected audio artifact could not be found.",
                status_code=404,
                details=str(source),
            )

        destination = Path(payload["destinationPath"])
        format_name = str(payload["format"]).lower()
        work_dir = self.storage.job_dir(make_id("export"))
        prepared = self.audio_pipeline.prepare_input(source, work_dir, stem="export_input")
        self.audio_pipeline.export(prepared.path, destination, fmt=format_name)
        artifact = self.audio_pipeline.inspect_audio(destination, kind="export", label=destination.stem.replace("_", " ").title())
        payload = artifact.model_dump(by_alias=True, mode="json")
        payload["createdAt"] = utc_now_iso()
        return payload
