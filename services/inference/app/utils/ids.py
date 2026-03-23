from __future__ import annotations

from datetime import datetime, timezone
from secrets import token_hex


def make_id(prefix: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{prefix}_{timestamp}_{token_hex(4)}"
