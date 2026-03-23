from __future__ import annotations

from dataclasses import asdict
from time import monotonic

from app import __version__
from app.config import AppConfig
from app.runtime import detect_capabilities


class HealthService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.started_at = monotonic()

    async def get_health(self) -> dict[str, object]:
        paths = self.config.paths
        return {
            "status": "ok",
            "version": __version__,
            "providers": [asdict(cap) for cap in detect_capabilities(self.config)],
            "paths": {
                "profiles": str(paths.profiles),
                "exports": str(paths.exports),
                "cache": str(paths.cache),
            },
            "uptimeSeconds": round(monotonic() - self.started_at, 2),
        }
