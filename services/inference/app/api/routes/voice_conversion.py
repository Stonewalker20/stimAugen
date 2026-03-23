from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import ServiceContainer, get_services
from app.models.voice_conversion import VoiceConversionAcceptedResponse, VoiceConversionRequest

router = APIRouter(prefix="/voice-conversion", tags=["voice-conversion"])


@router.post("", response_model=VoiceConversionAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_voice_conversion(
    request: VoiceConversionRequest,
    services: ServiceContainer = Depends(get_services),
) -> object:
    job = await services.voice_conversion_service.submit(request)
    return {"job": job}
