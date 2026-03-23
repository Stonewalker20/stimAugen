from __future__ import annotations

import asyncio

from app.config import AppConfig
from app.runtime import RuntimeCapability
from app.services.health_service import HealthService


def test_health_reports_readiness_and_optional_warnings(monkeypatch, tmp_path) -> None:
    config = AppConfig(data_root=tmp_path)
    config.paths.ensure()
    service = HealthService(config)

    monkeypatch.setattr(
        "app.services.health_service.detect_capabilities",
        lambda _: [
            RuntimeCapability("python", "Python Runtime", True, detail="Test runtime"),
            RuntimeCapability("ffmpeg", "FFmpeg", False, detail="not installed"),
        ],
    )

    payload = asyncio.run(service.get_health())

    assert payload["status"] == "ok"
    assert payload["diagnostics"]["ready"] is True
    assert payload["diagnostics"]["dataRoot"] == str(tmp_path)
    assert any(check["id"] == "data_root" and check["ok"] for check in payload["diagnostics"]["checks"])
    assert payload["diagnostics"]["warnings"] == ["FFmpeg is unavailable: not installed"]
