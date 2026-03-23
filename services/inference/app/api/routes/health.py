from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import ServiceContainer, get_services
from app.models.health import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def get_health(services: ServiceContainer = Depends(get_services)) -> object:
    return await services.health_service.get_health()
