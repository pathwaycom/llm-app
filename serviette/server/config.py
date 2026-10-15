"""Config loading/validation for the server command."""

from __future__ import annotations

from pathlib import Path

from serviette.config.schema import ServietteConfig, load_config


def load_server_config(path: str | Path) -> ServietteConfig:
    """Load a config file and assert it has what the server needs."""

    return load_config(path).for_server()
