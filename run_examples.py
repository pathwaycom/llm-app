#!/usr/bin/env python

"""
This is the main entrypoint for running all examples with centralized configuration.
However, all examples are self-contained and can also be run directly.
"""

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
        help="Rest input connector host.",
    )
    @click.option(
        "--port",
        "-p",
        envvar="PATHWAY_REST_CONNECTOR_PORT",
        type=int,
        default=8080,
        help="Rest input connector port.",
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
        envvar="PATHWAY_PERSISTENT_STORAGE",
        type=str,
        default="/tmp/cache",
    )
    @click.option(
        "--embedder_locator",
        "-e",
        envvar="EMBEDDER_LOCATOR",
        type=str,
        required=False,
        help="Embedding model locator.",
    )
    @click.option(
        "--embedding_dimension",
        "-d",
        envvar="EMBEDDING_DIMENSION",
        type=int,
        required=False,
        help="Embedding model output dimension.",
    )
    @click.option(
        "--max_tokens",
        "-x",
        envvar="MAX_OUTPUT_TOKENS",
        type=int,
        required=False,
        help="Maximum output tokens of the LLM.",
    )
    @click.option(
        "--model_locator",
        "-m",
        envvar="MODEL_LOCATOR",
        type=str,
        required=False,
        help="LLM locator for text completion/generation.",
    )
    @click.option(
        "--api_key",
        "-k",
        envvar="OPENAI_API_KEY",
        type=str,
        required=False,
        help="API Key for OpenAI/HuggingFace Inference APIs.",
    )
    @click.option(
        "--temperature",
        "-t",
        envvar="MODEL_TEMPERATURE",
        type=float,
        required=False,
        help="LLM temperature, controls the randomness of the outputs.",
    )
    @click.option(
        "--device",
        envvar="DEVICE",
        type=str,
        required=False,
        help="Device to run models on, e.g. 'cpu', 'cuda'",
    )
    @functools.wraps(func)
    def wrapper(**kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        return func(**kwargs)

    return wrapper


@cli.command()
@common_options
def local(**kwargs):
    from examples.pipelines.local import run

    return run(**kwargs)


@cli.command()
@common_options
def contextful(**kwargs):
    from examples.pipelines.contextful import run

    return run(**kwargs)


@cli.command()
@common_options
def s3(**kwargs):
    from examples.pipelines.contextful_s3 import run

    return run(**kwargs)


@cli.command()
@common_options
def contextful_s3(**kwargs):
    from examples.pipelines.contextful_s3 import run

    return run(**kwargs)


@cli.command()
@common_options
def contextless(**kwargs):
    from examples.pipelines.contextless import run

    return run(**kwargs)


@cli.command()
@common_options
def unstructured(**kwargs):
    from examples.pipelines.unstructured import run

    return run(**kwargs)


@cli.command()
@common_options
def unstructuredtosql(**kwargs):
    from examples.pipelines.unstructured_to_sql_on_the_fly import run

    return run(**kwargs)


@cli.command()
@common_options
def unstructured_to_sql(**kwargs):
    from examples.pipelines.unstructured_to_sql_on_the_fly import run

    return run(**kwargs)


@cli.command()
@common_options
def alert(**kwargs):
    from examples.pipelines.alert import run

    return run(**kwargs)


@cli.command()
@common_options
def drivealert(**kwargs):
    from examples.pipelines.drive_alert import run

    return run(**kwargs)


@cli.command()
@common_options
def drive_alert(**kwargs):
    from examples.pipelines.drive_alert import run

    return run(**kwargs)


@cli.command()
@common_options
def contextful_geometric(**kwargs):
    from examples.pipelines.contextful_geometric import run

    return run(**kwargs)


@cli.command()
@common_options
def geometric(**kwargs):
    from examples.pipelines.contextful_geometric import run

    return run(**kwargs)


def main():
    cli.main()


if __name__ == "__main__":
    cli.main()
