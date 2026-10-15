"""Config loading/validation for the indexer command."""

from __future__ import annotations

from pathlib import Path

from serviette.config.schema import ServietteConfig, load_config


def load_indexer_config(path: str | Path) -> ServietteConfig:
    """Load a config file and assert it has what the indexer needs."""

    return load_config(path).for_indexer()
