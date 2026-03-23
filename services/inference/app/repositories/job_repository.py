from __future__ import annotations

from app.services.storage import StorageService


class JobRepository:
    def __init__(self, storage: StorageService) -> None:
        self.storage = storage
        self.index_path = storage.jobs_index_path()

    def _read_index(self) -> list[dict[str, object]]:
        payload = self.storage.read_json(self.index_path, [])
        if isinstance(payload, list):
            return payload
        return []

    def _write_index(self, jobs: list[dict[str, object]]) -> None:
        self.storage.write_json(self.index_path, jobs)

    def upsert_job(self, job: dict[str, object]) -> dict[str, object]:
        jobs = self._read_index()
        updated = False
        for index, existing in enumerate(jobs):
            if existing.get("id") == job["id"]:
                jobs[index] = job
                updated = True
                break
        if not updated:
            jobs.append(job)
        jobs.sort(key=lambda item: str(item.get("createdAt", "")), reverse=True)
        self._write_index(jobs)
        self.storage.write_json(self.storage.job_manifest(str(job["id"])), job)
        return job

    def get_job(self, job_id: str) -> dict[str, object] | None:
        payload = self.storage.read_json(self.storage.job_manifest(job_id), None)
        if isinstance(payload, dict):
            return payload
        for job in self._read_index():
            if job.get("id") == job_id:
                return job
        return None

    def list_jobs(self, *, kind: str | None = None, status: str | None = None, limit: int = 50) -> list[dict[str, object]]:
        jobs = self._read_index()
        if kind:
            jobs = [job for job in jobs if job.get("kind") == kind]
        if status:
            jobs = [job for job in jobs if job.get("status") == status]
        return jobs[:limit]
