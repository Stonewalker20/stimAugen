from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from app import cli


def test_cli_sets_data_root_and_runs_uvicorn(monkeypatch, tmp_path) -> None:
    run = Mock()
    env: dict[str, str] = {}

    monkeypatch.setattr(cli.uvicorn, "run", run)
    monkeypatch.setattr(cli.os, "environ", env)
    monkeypatch.setattr(
        cli,
        "build_parser",
        lambda: SimpleNamespace(
            parse_args=lambda: SimpleNamespace(
                host="127.0.0.1",
                port=43127,
                log_level="warning",
                data_root=str(tmp_path),
            )
        ),
    )

    cli.main()

    assert env["HVS_DATA_ROOT"] == str(tmp_path)
    assert env["HOME_VOICE_STUDIO_DATA_ROOT"] == str(tmp_path)
    run.assert_called_once_with(
        "app.main:app",
        host="127.0.0.1",
        port=43127,
        log_level="warning",
    )
