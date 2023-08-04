#!/usr/bin/env python

import importlib
from typing import Optional

import click
from dotenv import load_dotenv

load_dotenv()


@click.group
def cli() -> None:
    pass


@cli.command()
@click.option(
    "--variant",
    envvar="APP_VARIANT",
    type=str,
    default="contextful",
    help="The app variant to run",
)
@click.option(
    "--host",
    "-h",
    envvar="PATHWAY_REST_CONNECTOR_HOST",
    type=str,
    default="127.0.0.1",
    help="Rest input connector host",
)
@click.option(
    "--port",
    "-p",
    envvar="PATHWAY_REST_CONNECTOR_PORT",
    type=int,
    default=8080,
    help="Rest input connector port",
)
@click.option(
    "--api_key",
    "-k",
    envvar="OPENAI_API_TOKEN",
    type=str,
    default="",
    help="API Key for OpenAI/HuggingFace Inference APIs",
)
@click.option(
    "--data_dir",
    envvar="PATHWAY_DATA_DIR",
    type=str,
    required=False,
)
@click.option(
    "--cache_dir",
    "-c",
    envvar="PATHWAY_CACHE_DIR",
    type=str,
    default="/tmp/cache",
)
@click.option(
    "--model_locator",
    "-m",
    envvar="MODEL_LOCATOR",
    type=str,
    required=False,
    help="LLM locator for text completion/generation",
)
@click.option(
    "--embedder_locator",
    "-e",
    envvar="EMBEDDER_LOCATOR",
    type=str,
    required=False,
    help="Embedding model locator. Default is ADA from OpenAI",
)
@click.option(
    "--embedding_dimension",
    "-d",
    envvar="EMBEDDING_DIMENSION",
    type=int,
    required=False,
    help="Embedding model output dimension. Default is for OpenAI/ADA",
)
@click.option(
    "--max_tokens",
    "-m",
    envvar="MAX_OUTPUT_TOKENS",
    type=int,
    required=False,
    help="Maximum output tokens of the LLM",
)
@click.option(
    "--temperature",
    "-t",
    envvar="MODEL_TEMPERATURE",
    type=float,
    required=False,
    help="LLM temperature, controls the randomness of the outputs.",
)
def up(
    *,
    variant: str,
    host: str,
    port: int,
    api_key: str,
    data_dir: str,
    cache_dir: str,
    model_locator: Optional[str],
    embedder_locator: Optional[str],
    embedding_dimension: Optional[int],
    max_tokens: Optional[int],
    temperature: Optional[float],
):
    args = {k: v for k, v in locals().items() if v is not None}
    scenario_module = importlib.import_module(f"pipelines.{variant}.app")
    scenario_module.run(**args)


def main():
    cli.main()


if __name__ == "__main__":
    cli.main()
