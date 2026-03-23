from __future__ import annotations

import shutil
from pathlib import Path

from app.config import AppPaths
from app.utils.json_io import read_json, write_json


class StorageService:
    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths
        self.paths.ensure()

    def read_json(self, path: Path, default: object) -> object:
        return read_json(path, default)

    def write_json(self, path: Path, payload: object) -> None:
        write_json(path, payload)

    def profile_dir(self, profile_id: str) -> Path:
        path = self.paths.profiles / profile_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def profile_manifest(self, profile_id: str) -> Path:
        return self.profile_dir(profile_id) / "profile.json"

    def copy_reference_clip(self, profile_id: str, source_path: str) -> Path:
        source = Path(source_path).expanduser().resolve()
        destination = self.profile_dir(profile_id) / "references" / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return destination

    def jobs_index_path(self) -> Path:
        return self.paths.jobs / "index.json"

    def job_dir(self, job_id: str) -> Path:
        path = self.paths.jobs / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def job_manifest(self, job_id: str) -> Path:
        return self.job_dir(job_id) / "job.json"

    def job_artifact_path(self, job_id: str, stem: str, extension: str) -> Path:
        filename = f"{stem}.{extension.lstrip('.')}"
        return self.job_dir(job_id) / filename

    def job_waveform_path(self, job_id: str, name: str = "waveform") -> Path:
        return self.job_artifact_path(job_id, name, "json")

    def cleanup_job_dir(self, job_id: str, keep: set[str] | None = None) -> None:
        keep = keep or set()
        job_dir = self.job_dir(job_id)
        for child in job_dir.iterdir():
            if str(child) in keep:
                continue
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)

