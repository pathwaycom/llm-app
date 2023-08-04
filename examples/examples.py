#!/usr/bin/env python

import functools

import click
from dotenv import load_dotenv

load_dotenv()


@click.group
def cli() -> None:
    pass


def common_options(func):
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
        "--model_locator",
        "-m",
        envvar="MODEL_LOCATOR",
        type=str,
        required=False,
        help="LLM locator for text completion/generation",
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
        "--temperature",
        "-t",
        envvar="MODEL_TEMPERATURE",
        type=float,
        required=False,
        help="LLM temperature, controls the randomness of the outputs.",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@cli.command()
@common_options
def local(**kwargs):
    from pipelines.local import run

    return run(**kwargs)


@cli.command()
@common_options
def contextful(**kwargs):
    from pipelines.contextful import run

    return run(**kwargs)


@cli.command()
@common_options
def contextful_s3(**kwargs):
    from pipelines.contextful_s3 import run

    return run(**kwargs)


@cli.command()
@common_options
def contextless(**kwargs):
    from pipelines.contextless import run

    return run(**kwargs)


def main():
    cli.main()


if __name__ == "__main__":
    cli.main()
