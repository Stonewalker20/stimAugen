from __future__ import annotations

import os
from pathlib import Path
from time import monotonic

from app import __version__
from app.config import AppConfig
from app.models.health import HealthCheck
from app.runtime import detect_capabilities


class HealthService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.started_at = monotonic()

    def _path_check(self, identifier: str, label: str, path: Path) -> HealthCheck:
        exists = path.exists()
        is_directory = path.is_dir()
        writable = exists and is_directory and os.access(path, os.W_OK | os.X_OK)
        if not exists:
            detail = f"{path} does not exist"
        elif not is_directory:
            detail = f"{path} is not a directory"
        elif not writable:
            detail = f"{path} is not writable"
        else:
            detail = str(path)
        return HealthCheck(id=identifier, label=label, ok=bool(exists and is_directory and writable), detail=detail)

    async def get_health(self) -> dict[str, object]:
        paths = self.config.paths
        capabilities = detect_capabilities(self.config)
        visible_providers = [
            {
                "id": cap.id,
                "label": cap.label,
                "available": cap.available,
                "detail": cap.detail,
            }
            for cap in capabilities
            if cap.user_visible
        ]
        path_checks = [
            self._path_check("data_root", "Data root", paths.root),
            self._path_check("profiles", "Profiles directory", paths.profiles),
            self._path_check("exports", "Exports directory", paths.exports),
            self._path_check("cache", "Cache directory", paths.cache),
            self._path_check("jobs", "Jobs cache", paths.jobs),
            self._path_check("settings", "Settings parent directory", paths.settings.parent),
            self._path_check("logs", "Logs directory", paths.logs),
        ]
        warnings = [
            f"{cap.label} is unavailable: {cap.detail}" if cap.detail else f"{cap.label} is unavailable"
            for cap in capabilities
            if not cap.available and not cap.required
        ]
        required_capabilities_ready = all(cap.available for cap in capabilities if cap.required)
        ready = all(check.ok for check in path_checks) and required_capabilities_ready
        return {
            "status": "ok" if ready else "degraded",
            "version": __version__,
            "providers": visible_providers,
            "paths": {
                "profiles": str(paths.profiles),
                "exports": str(paths.exports),
                "cache": str(paths.cache),
            },
            "diagnostics": {
                "ready": ready,
                "dataRoot": str(paths.root),
                "checks": [check.model_dump(by_alias=True) for check in path_checks],
                "warnings": warnings,
            },
            "uptimeSeconds": round(monotonic() - self.started_at, 2),
        }
