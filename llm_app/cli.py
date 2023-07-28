from typing import NoReturn
import click
from llm_app.main import run


@click.group
def cli() -> None:
    pass


@click.command()
def up():
    return run()


def main() -> NoReturn:
    cli.main()
