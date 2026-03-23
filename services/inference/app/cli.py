from __future__ import annotations

import argparse
import os

from app.main import app as application
import uvicorn


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="home-voice-studio-inference",
        description="Launch the Home Voice Studio local inference API.",
    )
    parser.add_argument("--host", default=os.environ.get("HVS_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("HVS_PORT", "43127")))
    parser.add_argument("--log-level", default=os.environ.get("HVS_LOG_LEVEL", "info"))
    parser.add_argument(
        "--data-root",
        default=os.environ.get("HVS_DATA_ROOT") or os.environ.get("HOME_VOICE_STUDIO_DATA_ROOT"),
        help="Optional override for the local app data directory.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.data_root:
        os.environ["HVS_DATA_ROOT"] = args.data_root
        os.environ["HOME_VOICE_STUDIO_DATA_ROOT"] = args.data_root

    uvicorn.run(
        application,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
