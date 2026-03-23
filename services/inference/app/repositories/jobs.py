from __future__ import annotations

import json
from pathlib import Path

from app.models.jobs import JobResponse


class JobRepository:
    def __init__(self, jobs_dir: Path) -> None:
        self._jobs_dir = jobs_dir
        self._jobs_dir.mkdir(parents=True, exist_ok=True)

    def job_dir(self, job_id: str) -> Path:
        path = self._jobs_dir / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _job_path(self, job_id: str) -> Path:
        return self.job_dir(job_id) / "job.json"

    async def save(self, job: JobResponse) -> JobResponse:
        with self._job_path(job.id).open("w", encoding="utf-8") as handle:
            json.dump(job.model_dump(mode="json", by_alias=True), handle, indent=2)
        return job

    async def get(self, job_id: str) -> JobResponse | None:
        job_path = self._job_path(job_id)
        if not job_path.exists():
            return None
        with job_path.open("r", encoding="utf-8") as handle:
            return JobResponse.model_validate(json.load(handle))

    async def list(self, *, kind: str | None = None, status: str | None = None, limit: int = 50) -> list[JobResponse]:
        jobs: list[JobResponse] = []
        for job_path in sorted(self._jobs_dir.glob("*/job.json"), reverse=True):
            with job_path.open("r", encoding="utf-8") as handle:
                job = JobResponse.model_validate(json.load(handle))
            if kind and job.kind != kind:
                continue
            if status and job.status != status:
                continue
            jobs.append(job)
            if len(jobs) >= limit:
                break
        return jobs
