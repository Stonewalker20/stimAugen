from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import ServiceContainer, get_services
from app.models.exports import ExportRequest, ExportResponse

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("", response_model=ExportResponse, status_code=status.HTTP_201_CREATED)
async def export_artifact(request: ExportRequest, services: ServiceContainer = Depends(get_services)) -> object:
    artifact = await services.export_service.export_artifact(request)
    return {"artifact": artifact}
