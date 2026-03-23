from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import ServiceContainer, get_services
from app.models.settings import AppSettings, SettingsResponse

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(services: ServiceContainer = Depends(get_services)) -> object:
    settings = await services.settings_service.get_settings()
    return {"settings": settings}


@router.put("", response_model=SettingsResponse)
async def update_settings(request: AppSettings, services: ServiceContainer = Depends(get_services)) -> object:
    settings = await services.settings_service.update_settings(request)
    return {"settings": settings}
