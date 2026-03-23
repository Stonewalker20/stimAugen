from __future__ import annotations

from functools import lru_cache

from .container import AppContainer


@lru_cache(maxsize=1)
def get_container() -> AppContainer:
    return AppContainer()
