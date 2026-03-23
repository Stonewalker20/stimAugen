from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import ServiceContainer, get_services
from app.models.tts import TtsAcceptedResponse, TtsRequest

router = APIRouter(prefix="/tts", tags=["tts"])


@router.post("", response_model=TtsAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_tts(request: TtsRequest, services: ServiceContainer = Depends(get_services)) -> object:
    job = await services.tts_service.submit(request)
    return {"job": job}
