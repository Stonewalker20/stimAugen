from __future__ import annotations

from pathlib import Path

from app.models.common import AudioArtifact
from app.services.storage import StorageService


class ArtifactRepository:
    def __init__(self, storage: StorageService) -> None:
        self.storage = storage
        self.storage.ensure_artifact_layout()

    def save_artifact(self, artifact: AudioArtifact) -> AudioArtifact:
        self.storage.write_json(self.storage.artifact_metadata_path(artifact.id), artifact.model_dump(mode="json", by_alias=True))
        return artifact

    def get_artifact(self, artifact_id: str) -> AudioArtifact:
        payload = self.storage.read_json(self.storage.artifact_metadata_path(artifact_id))
        if payload is None:
            raise FileNotFoundError(artifact_id)
        return AudioArtifact.model_validate(payload)

    def list_artifacts(self) -> list[AudioArtifact]:
        artifacts: list[AudioArtifact] = []
        for path in self.storage.list_artifact_metadata_paths():
            payload = self.storage.read_json(path)
            if payload is None:
                continue
            artifacts.append(AudioArtifact.model_validate(payload))
        artifacts.sort(key=lambda item: item.created_at, reverse=True)
        return artifacts

    def delete_artifact(self, artifact_id: str) -> None:
        self.storage.artifact_metadata_path(artifact_id).unlink(missing_ok=True)
