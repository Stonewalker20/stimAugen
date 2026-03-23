from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


def _default_root() -> Path:
    return Path(os.getenv("HVS_DATA_ROOT", Path.cwd() / "data")).resolve()


@dataclass(frozen=True)
class AppPaths:
    root: Path
    profiles: Path
    exports: Path
    cache: Path
    jobs: Path
    settings: Path
    logs: Path

    @classmethod
    def create(cls, root: Path | None = None) -> "AppPaths":
        base = (root or _default_root()).resolve()
        return cls(
            root=base,
            profiles=base / "profiles",
            exports=base / "exports",
            cache=base / "cache",
            jobs=base / "cache" / "jobs",
            settings=base / "settings.json",
            logs=base / "logs",
        )

    def ensure(self) -> None:
        for directory in (self.root, self.profiles, self.exports, self.cache, self.jobs, self.logs):
            directory.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class AppConfig:
    host: str = os.getenv("HVS_HOST", "127.0.0.1")
    port: int = int(os.getenv("HVS_PORT", "8765"))
    data_root: Path = _default_root()
    app_name: str = "Home Voice Studio Inference"
    preview_duration_limit_ms: int = int(os.getenv("HVS_PREVIEW_DURATION_MS", "45000"))

    @property
    def paths(self) -> AppPaths:
        return AppPaths.create(self.data_root)


def load_config() -> AppConfig:
    config = AppConfig()
    config.paths.ensure()
    return config
