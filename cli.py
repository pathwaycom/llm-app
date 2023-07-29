import click
from dotenv import load_dotenv
from llm_app.main import run
from llm_app.config import Config


load_dotenv()


@click.group()
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
    default="./data/pathway-docs/",
)
@click.option(
    "--cache_dir",
    "-c",
    envvar="PATHWAY_CACHE_DIR",
    type=str,
    default="/tmp/cache",
)
@click.option(
    "--model",
    "-m",
    envvar="MODEL_LOCATOR",
    type=str,
    default="gpt-3.5-turbo",
    help="LLM locator for text completion/generation",
)
@click.option(
    "--embedder",
    "-e",
    envvar="EMBEDDER_LOCATOR",
    type=str,
    default="text-embedding-ada-002",
    help="Embedding model locator. Default is ADA from OpenAI",
)
@click.option(
    "--embedding_dim",
    "-d",
    envvar="EMBEDDING_DIMENSION",
    type=int,
    default=1536,
    help="Embedding model output dimension. Default is for OpenAI/ADA",
)
@click.option(
    "--max_tokens",
    "-m",
    envvar="MAX_OUTPUT_TOKENS",
    type=int,
    default=60,
    help="Maximum output tokens of the LLM",
)
@click.option(
    "--temperature",
    "-t",
    envvar="MODEL_TEMPERATURE",
    type=float,
    default=0.8,
    help="LLM temperature, controls the randomness of the outputs.",
)
def up(
    variant: str,
    host: str,
    port: int,
    api_key: str,
    data_dir: str,
    cache_dir: str,
    model: str,
    embedder: str,
    embedding_dim: int,
    max_tokens: int,
    temperature: float,
):
    config = Config(
        app_variant=variant,
        rest_host=host,
        rest_port=port,
        api_key=api_key,
        cache_dir=cache_dir,
        model_locator=model,
        data_dir=data_dir,
        embedder_locator=embedder,
        embedding_dimension=embedding_dim,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return run(config)


if __name__ == "__main__":
    cli.main()
