#!/usr/bin/env python3
"""Bootstrap local model placeholders for Home Voice Studio.

The MVP does not depend on any specific hosted model. This script only
creates the local directories and metadata stubs expected by the runtime.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "data" / "models"
MANIFEST = MODELS_DIR / "manifest.json"


def ensure_manifest() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if MANIFEST.exists():
        return

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "status": "placeholder",
        "notes": [
            "Populate this manifest with local model paths or provider metadata.",
            "Keep model-specific integration behind the stable provider interfaces.",
        ],
    }
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def check() -> int:
    ensure_manifest()
    print("Local model bootstrap check")
    print(f"models dir: {MODELS_DIR}")
    print(f"manifest: {MANIFEST}")
    print("status: placeholder manifest present")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify the local model bootstrap state")
    parser.add_argument("--init", action="store_true", help="Create placeholder model metadata")
    args = parser.parse_args(argv)

    if args.check or args.init:
        return check()

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
