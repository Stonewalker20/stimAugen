from __future__ import annotations

import asyncio
from pathlib import Path

from app.api.errors import AppError
from app.config import AppPaths
from app.repositories import JobRepository
from app.services.jobs import JobManager
from app.services.storage import StorageService


def test_cancel_job_is_immediate_and_idempotent(tmp_path: Path) -> None:
    async def scenario() -> None:
        paths = AppPaths.create(tmp_path / "data")
        storage = StorageService(paths)
        repository = JobRepository(storage)
        manager = JobManager(repository, storage)
        started = asyncio.Event()

        async def runner(job_id: str, payload: dict[str, object], update_progress):
            started.set()
            await update_progress(12)
            await asyncio.sleep(1)
            return {"result": {"jobId": job_id, "payload": payload}, "artifacts": []}

        try:
            accepted = await manager.submit("tts", {"text": "cancel me"}, runner)
            assert accepted["status"] == "queued"

            for _ in range(50):
                current = await manager.get_job(accepted["jobId"])
                if current["status"] == "running":
                    break
                await asyncio.sleep(0.02)

            await started.wait()
            cancelled = await manager.cancel_job(accepted["jobId"])
            assert cancelled["status"] == "cancelled"
            assert cancelled["cancelRequestedAt"] is not None

            current = await manager.get_job(accepted["jobId"])
            assert current["status"] == "cancelled"
            assert current["cancelRequestedAt"] is not None

            cancelled_again = await manager.cancel_job(accepted["jobId"])
            assert cancelled_again["status"] == "cancelled"
            assert cancelled_again["cancelRequestedAt"] is not None
        finally:
            await manager.shutdown()

    asyncio.run(scenario())


def test_retryable_job_retries_and_completes(tmp_path: Path) -> None:
    async def scenario() -> None:
        paths = AppPaths.create(tmp_path / "data")
        storage = StorageService(paths)
        repository = JobRepository(storage)
        manager = JobManager(repository, storage)
        attempts = 0

        async def runner(job_id: str, payload: dict[str, object], update_progress):
            nonlocal attempts
            attempts += 1
            await update_progress(25)
            if attempts == 1:
                raise AppError("temporary_failure", "Try again.", retryable=True)
            await update_progress(75)
            return {"result": {"jobId": job_id, "payload": payload}, "artifacts": []}

        try:
            accepted = await manager.submit("tts", {"text": "retry me", "maxAttempts": 2}, runner)

            for _ in range(100):
                current = await manager.get_job(accepted["jobId"])
                if current["status"] == "completed":
                    break
                await asyncio.sleep(0.02)

            current = await manager.get_job(accepted["jobId"])
            assert current["status"] == "completed"
            assert current["attemptCount"] == 2
            assert current["retryCount"] == 1
            assert attempts == 2
        finally:
            await manager.shutdown()

    asyncio.run(scenario())
