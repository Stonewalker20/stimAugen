from __future__ import annotations

from dataclasses import dataclass
import os

from .config import AppConfig
from .utils.process import command_exists


@dataclass(frozen=True)
class RuntimeCapability:
    id: str
    label: str
    available: bool
    required: bool = True
    user_visible: bool = True
    detail: str | None = None


def detect_capabilities(config: AppConfig) -> list[RuntimeCapability]:
    ffmpeg_available = command_exists("ffmpeg")
    runtime_mode = os.getenv("HVS_RUNTIME_MODE", "development")
    speech_detail = (
        "Native desktop speech is available on this machine."
        if command_exists("say") or command_exists("powershell")
        else "Built-in local fallback speech is available. Native desktop voices can be added later."
    )
    return [
        RuntimeCapability(
            "speech_generation",
            "Speak Text",
            True,
            detail=speech_detail,
        ),
        RuntimeCapability(
            "voice_change",
            "Change Voice",
            True,
            detail="Offline voice change is available for uploaded recordings.",
        ),
        RuntimeCapability(
            "clean_recording",
            "Clean Recording",
            True,
            detail="Local cleanup modes are ready for denoise, voice focus, and vocal isolation.",
        ),
        RuntimeCapability(
            "mp3_export",
            "MP3 Export",
            ffmpeg_available,
            required=False,
            user_visible=False,
            detail=(
                "FFmpeg is available for MP3 export."
                if ffmpeg_available
                else (
                    "Install FFmpeg to enable MP3 export. WAV export already works in development."
                    if runtime_mode == "development"
                    else "Install or bundle FFmpeg to enable MP3 export. WAV export already works."
                )
            ),
        ),
    ]
