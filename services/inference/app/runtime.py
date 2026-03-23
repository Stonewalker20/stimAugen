from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig
from .utils.process import command_exists


@dataclass(frozen=True)
class RuntimeCapability:
    id: str
    label: str
    available: bool
    detail: str | None = None


def detect_capabilities(config: AppConfig) -> list[RuntimeCapability]:
    return [
        RuntimeCapability("python", "Python Runtime", True, detail=config.app_name),
        RuntimeCapability("ffmpeg", "FFmpeg", command_exists("ffmpeg"), detail="Required for high-quality transcoding"),
        RuntimeCapability("say", "macOS Say", command_exists("say"), detail="Used for native macOS speech synthesis"),
        RuntimeCapability("powershell", "PowerShell", command_exists("powershell"), detail="Used for Windows speech synthesis"),
    ]
