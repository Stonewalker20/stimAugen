from __future__ import annotations

import json
from pathlib import Path

from app.models.profiles import VoiceProfile


class ProfileRepository:
    def __init__(self, profiles_dir: Path) -> None:
        self._profiles_dir = profiles_dir
        self._profiles_dir.mkdir(parents=True, exist_ok=True)

    def _profile_path(self, profile_id: str) -> Path:
        return self._profiles_dir / profile_id / "profile.json"

    async def list_profiles(self) -> list[VoiceProfile]:
        profiles: list[VoiceProfile] = []
        for profile_path in sorted(self._profiles_dir.glob("*/profile.json")):
            with profile_path.open("r", encoding="utf-8") as handle:
                profiles.append(VoiceProfile.model_validate(json.load(handle)))
        return profiles

    async def get_profile(self, profile_id: str) -> VoiceProfile | None:
        profile_path = self._profile_path(profile_id)
        if not profile_path.exists():
            return None
        with profile_path.open("r", encoding="utf-8") as handle:
            return VoiceProfile.model_validate(json.load(handle))

    async def save_profile(self, profile: VoiceProfile) -> VoiceProfile:
        profile_dir = self._profiles_dir / profile.id
        profile_dir.mkdir(parents=True, exist_ok=True)
        with self._profile_path(profile.id).open("w", encoding="utf-8") as handle:
            json.dump(profile.model_dump(mode="json", by_alias=True), handle, indent=2)
        return profile
