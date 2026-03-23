from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import ServiceContainer, get_services
from app.models.jobs import CancelJobResponse, JobListResponse, JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    services: ServiceContainer = Depends(get_services),
    kind: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> object:
    jobs = await services.job_service.list_jobs(kind=kind, status=status, limit=limit)
    return {"jobs": jobs}


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, services: ServiceContainer = Depends(get_services)) -> object:
    return await services.job_service.get_job(job_id)


@router.post("/{job_id}/cancel", response_model=CancelJobResponse)
async def cancel_job(job_id: str, services: ServiceContainer = Depends(get_services)) -> object:
    return await services.job_service.cancel_job(job_id)
