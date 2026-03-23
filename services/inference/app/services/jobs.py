from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from app.api.errors import AppError, NotFoundError
from app.services.storage import StorageService
from app.utils.clock import utc_now_iso
from app.utils.ids import make_id

JobRunner = Callable[[str, dict[str, object], Callable[[int], Awaitable[None]]], Awaitable[dict[str, object]]]

TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


class JobManager:
    def __init__(self, job_repository: object, storage: StorageService) -> None:
        self.job_repository = job_repository
        self.storage = storage
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()

    async def submit(self, kind: str, request_payload: dict[str, object], runner: JobRunner) -> dict[str, object]:
        job_id = make_id("job")
        requested_attempts = request_payload.get("maxAttempts", 1)
        try:
            max_attempts = max(1, min(3, int(requested_attempts)))
        except (TypeError, ValueError):
            max_attempts = 1
        job = {
            "id": job_id,
            "kind": kind,
            "status": "queued",
            "progress": 0,
            "attemptCount": 0,
            "maxAttempts": max_attempts,
            "retryCount": 0,
            "createdAt": utc_now_iso(),
            "startedAt": None,
            "finishedAt": None,
            "request": request_payload,
            "result": None,
            "error": None,
            "artifacts": [],
        }
        self.job_repository.upsert_job(job)
        task = asyncio.create_task(self._run_job(job_id, kind, request_payload, runner), name=job_id)
        self._tasks[job_id] = task
        return self._accepted(job)

    async def _run_job(self, job_id: str, kind: str, payload: dict[str, object], runner: JobRunner) -> None:
        current = self.job_repository.get_job(job_id) or {}
        max_attempts = max(1, int(current.get("maxAttempts", 1)))

        async def update_progress(value: int) -> None:
            await self._patch(job_id, progress=max(0, min(100, value)))

        try:
            for attempt in range(1, max_attempts + 1):
                await self._patch(
                    job_id,
                    status="running",
                    startedAt=current.get("startedAt") or utc_now_iso(),
                    progress=5,
                    attemptCount=attempt,
                    retryCount=max(0, attempt - 1),
                    finishedAt=None,
                )
                try:
                    result = await runner(job_id, payload, update_progress)
                    current = self.job_repository.get_job(job_id)
                    if current is not None and str(current.get("status")) == "cancelled":
                        return
                    await self._patch(
                        job_id,
                        status="completed",
                        progress=100,
                        finishedAt=utc_now_iso(),
                        result=result.get("result"),
                        artifacts=result.get("artifacts", []),
                        error=None,
                    )
                    return
                except AppError as exc:
                    if exc.error.retryable and attempt < max_attempts:
                        await self._patch(
                            job_id,
                            status="retrying",
                            progress=0,
                            error={
                                "code": exc.error.code,
                                "message": exc.error.message,
                                "details": exc.error.details,
                                "retryable": exc.error.retryable,
                            },
                        )
                        await asyncio.sleep(0)
                        continue
                    await self._patch(
                        job_id,
                        status="failed",
                        finishedAt=utc_now_iso(),
                        error={
                            "code": exc.error.code,
                            "message": exc.error.message,
                            "details": exc.error.details,
                            "retryable": exc.error.retryable,
                        },
                    )
                    return
                except Exception as exc:
                    await self._patch(
                        job_id,
                        status="failed",
                        finishedAt=utc_now_iso(),
                        error={
                            "code": "processing_failed",
                            "message": "The local processing job failed.",
                            "details": str(exc),
                            "retryable": False,
                        },
                    )
                    return
        except asyncio.CancelledError:
            self.storage.cleanup_job_dir(job_id)
            await self._patch(job_id, status="cancelled", finishedAt=utc_now_iso(), progress=0)
            raise
        finally:
            self._tasks.pop(job_id, None)

    async def _patch(self, job_id: str, **changes: object) -> dict[str, object]:
        async with self._lock:
            current = self.job_repository.get_job(job_id)
            if current is None:
                raise NotFoundError("job", job_id)
            current.update(changes)
            return self.job_repository.upsert_job(current)

    def _accepted(self, job: dict[str, object]) -> dict[str, object]:
        return {
            "jobId": job["id"],
            "kind": job["kind"],
            "status": job["status"],
            "progress": job["progress"],
            "createdAt": job["createdAt"],
            "pollUrl": f"/jobs/{job['id']}",
        }

    async def list_jobs(self, *, kind: str | None = None, status: str | None = None, limit: int = 50) -> list[dict[str, object]]:
        return self.job_repository.list_jobs(kind=kind, status=status, limit=limit)

    async def get_job(self, job_id: str) -> dict[str, object]:
        job = self.job_repository.get_job(job_id)
        if job is None:
            raise NotFoundError("job", job_id)
        return job

    async def cancel_job(self, job_id: str) -> dict[str, object]:
        task = self._tasks.get(job_id)
        current = self.job_repository.get_job(job_id)
        if current is None:
            raise NotFoundError("job", job_id)

        if str(current.get("status")) not in TERMINAL_STATUSES:
            cancelled_at = utc_now_iso()
            current.update(
                {
                    "status": "cancelled",
                    "progress": 0,
                    "finishedAt": cancelled_at,
                    "cancelRequestedAt": cancelled_at,
                    "error": None,
                }
            )
            self.job_repository.upsert_job(current)

        if task is not None:
            task.cancel()

        return {
            "id": current["id"],
            "status": current["status"],
            "cancelRequestedAt": current.get("cancelRequestedAt"),
        }

    async def shutdown(self) -> None:
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


class JobService:
    def __init__(self, manager: JobManager) -> None:
        self.manager = manager

    async def list_jobs(self, kind: str | None = None, status: str | None = None, limit: int = 50) -> object:
        return await self.manager.list_jobs(kind=kind, status=status, limit=limit)

    async def get_job(self, job_id: str) -> object:
        return await self.manager.get_job(job_id)

    async def cancel_job(self, job_id: str) -> object:
        return await self.manager.cancel_job(job_id)
