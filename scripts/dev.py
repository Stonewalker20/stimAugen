#!/usr/bin/env python3
"""Workspace helper commands for Home Voice Studio.

This script is intentionally stdlib-only so it can run before the app
dependencies are fully installed.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DIRS = [
    ROOT / "apps" / "desktop",
    ROOT / "services" / "inference",
    ROOT / "packages" / "shared-types",
    ROOT / "packages" / "ui",
    ROOT / "data" / "profiles",
    ROOT / "data" / "exports",
    ROOT / "data" / "cache",
]

EXPECTED_TOOLS = ["node", "python3", "cargo", "rustc", "ffmpeg"]


def tool_exists(name: str) -> bool:
    return shutil.which(name) is not None


def doctor() -> int:
    print("Home Voice Studio workspace doctor")
    print(f"root: {ROOT}")
    print()

    missing_dirs = [path for path in EXPECTED_DIRS if not path.exists()]
    if missing_dirs:
        print("Missing expected directories:")
        for path in missing_dirs:
            print(f"  - {path.relative_to(ROOT)}")
    else:
        print("Expected directories: ok")

    print()
    print("Toolchain:")
    for tool in EXPECTED_TOOLS:
        print(f"  - {tool}: {'ok' if tool_exists(tool) else 'missing'}")

    print()
    if missing_dirs:
        print("Workspace bootstrap is incomplete.")
        return 1

    print("Workspace bootstrap looks ready for app implementation.")
    return 0


def bootstrap() -> int:
    print("Bootstrapping workspace directories")
    for path in EXPECTED_DIRS:
        path.mkdir(parents=True, exist_ok=True)
        print(f"  - ensured {path.relative_to(ROOT)}")

    log_dir = ROOT / "data" / "cache" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    print(f"  - ensured {log_dir.relative_to(ROOT)}")

    jobs_dir = ROOT / "data" / "cache" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    print(f"  - ensured {jobs_dir.relative_to(ROOT)}")

    return 0


def bootstrap_models() -> int:
    print("Ensuring local model placeholders")
    return run_command([sys.executable, str(ROOT / "scripts" / "bootstrap_models.py"), "--check"])


def run_command(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> int:
    pretty = " ".join(command)
    location = f" (cwd={cwd})" if cwd else ""
    print(f"running: {pretty}{location}")
    completed = subprocess.run(command, cwd=cwd, env=env)
    return completed.returncode


def verify() -> int:
    print("Workspace verification")
    bootstrap_rc = bootstrap()
    if bootstrap_rc != 0:
        return bootstrap_rc

    models_bootstrap_rc = bootstrap_models()
    if models_bootstrap_rc != 0:
        return models_bootstrap_rc

    if doctor() != 0:
        return 1

    checks: list[tuple[list[str], Path | None, dict[str, str] | None]] = [
        (["npm", "run", "typecheck"], ROOT, None),
        (["npm", "run", "build"], ROOT, None),
        ([sys.executable, "-m", "pytest", "services/inference/tests", "-q"], ROOT, {"PYTHONPATH": "services/inference"}),
        ([sys.executable, "-m", "compileall", "services/inference/app", "services/inference/tests"], ROOT, None),
    ]

    for command, cwd, env_vars in checks:
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
        if run_command(command, cwd=cwd, env=env) != 0:
            return 1

    if tool_exists("cargo"):
        cargo_rc = run_command(["cargo", "check", "--manifest-path", "apps/desktop/src-tauri/Cargo.toml"], ROOT)
        if cargo_rc != 0:
            return cargo_rc
    else:
        print("cargo not found; skipping Rust desktop check")

    print("Verification completed")
    return 0


def status() -> int:
    print("Home Voice Studio workspace status")
    print(f"root: {ROOT}")
    print(f"data root: {os.environ.get('HVS_DATA_ROOT', ROOT / 'data')}")
    print(f"advanced mode: {os.environ.get('HVS_ADVANCED_MODE', 'false')}")
    print("expected run targets:")
    print("  - apps/desktop: Tauri React desktop app")
    print("  - services/inference: FastAPI sidecar")
    print("  - packages/shared-types: shared contracts")
    print("  - packages/ui: shared UI primitives")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("doctor", help="Check workspace directories and tools")
    subcommands.add_parser("status", help="Print workspace status")
    subcommands.add_parser("bootstrap", help="Create local data directories")
    subcommands.add_parser("bootstrap:models", help="Create local model placeholder metadata")
    subcommands.add_parser("verify", help="Run the current local verification stack")
    args = parser.parse_args(argv)

    if args.command == "doctor":
        return doctor()
    if args.command == "status":
        return status()
    if args.command == "bootstrap":
        return bootstrap()
    if args.command == "bootstrap:models":
        return bootstrap_models()
    if args.command == "verify":
        return verify()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
