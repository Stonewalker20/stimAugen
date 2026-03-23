from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import ServiceContainer, get_services
from app.models.profiles import (
    CreateProfileRequest,
    ProfileListResponse,
    ProfileMutationResponse,
    UpdateProfileRequest,
)

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("", response_model=ProfileListResponse)
async def list_profiles(services: ServiceContainer = Depends(get_services)) -> object:
    profiles = await services.profile_service.list_profiles()
    return {"profiles": profiles}


@router.post("", response_model=ProfileMutationResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(request: CreateProfileRequest, services: ServiceContainer = Depends(get_services)) -> object:
    profile = await services.profile_service.create_profile(request)
    return {"profile": profile}


@router.patch("/{profile_id}", response_model=ProfileMutationResponse)
async def update_profile(
    profile_id: str,
    request: UpdateProfileRequest,
    services: ServiceContainer = Depends(get_services),
) -> object:
    profile = await services.profile_service.update_profile(profile_id, request)
    return {"profile": profile}
