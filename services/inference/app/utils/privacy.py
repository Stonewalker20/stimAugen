from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import urlparse


DEFAULT_LOCAL_INFERENCE_HOST = "http://127.0.0.1:8765"
LOCAL_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def is_local_http_url(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    if parsed.scheme != "http":
        return False
    if parsed.username or parsed.password:
        return False
    host = parsed.hostname
    return host in LOCAL_LOOPBACK_HOSTS


def normalize_local_http_url(value: str | None, *, default: str = DEFAULT_LOCAL_INFERENCE_HOST) -> str:
    if not value:
        return default
    if not is_local_http_url(value):
        return default
    parsed = urlparse(value)
    host = parsed.hostname or "127.0.0.1"
    port = f":{parsed.port}" if parsed.port is not None else ""
    return f"http://{host}{port}"


def voice_cloning_allowed(profile: Mapping[str, object], settings: Mapping[str, object] | None = None) -> bool:
    if bool(profile.get("consentConfirmed")):
        return True
    if settings is None:
        return False
    return bool(settings.get("allowUnsafeVoiceCloning"))
