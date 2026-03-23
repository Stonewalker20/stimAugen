from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import ServiceContainer, get_services
from app.models.isolation import IsolationAcceptedResponse, IsolationRequest

router = APIRouter(prefix="/isolation", tags=["isolation"])


@router.post("", response_model=IsolationAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_isolation(request: IsolationRequest, services: ServiceContainer = Depends(get_services)) -> object:
    job = await services.isolation_service.submit(request)
    return {"job": job}
