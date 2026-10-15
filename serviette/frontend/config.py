"""Config loading/validation for the frontend command."""

from __future__ import annotations

from pathlib import Path

from serviette.config.schema import ServietteConfig, load_config


def load_frontend_config(path: str | Path) -> ServietteConfig:
    """Load a config file and assert it has a ``frontend`` section."""

    return load_config(path).for_frontend()
