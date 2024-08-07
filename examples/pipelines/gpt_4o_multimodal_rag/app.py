import logging
import os

# flake8: noqa
for tesseract_dir in [
    "/usr/share/tesseract/tessdata/",
    "/usr/share/tesseract-ocr/5/tessdata",
]:
    if os.path.exists(tesseract_dir):
        os.environ["TESSDATA_PREFIX"] = tesseract_dir  # fix for tesseract ocr
        break

import sys

import click
import pathway as pw
import pathway.io.fs as io_fs
import pathway.io.gdrive as io_gdrive
import yaml
from dotenv import load_dotenv
from pathway.udfs import DiskCache, ExponentialBackoffRetryStrategy
from pathway.xpacks.llm import embedders, llms, prompts  # , parsers, splitters
from pathway.xpacks.llm.parsers import OpenParse
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from pathway.xpacks.llm.vector_store import VectorStoreServer

# To use advanced features with Pathway Scale, get your free license key from
# https://pathway.com/features and paste it below.
# To use Pathway Community, comment out the line below.
pw.set_license_key("demo-license-key-with-telemetry")

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def data_sources(source_configs) -> list[pw.Table]:
    sources = []
    for source_config in source_configs:
        if source_config["kind"] == "local":
            source = pw.io.fs.read(
                **source_config["config"],
                format="binary",
                with_metadata=True,
            )
            sources.append(source)
        elif source_config["kind"] == "gdrive":
            source = pw.io.gdrive.read(
                **source_config["config"],
                with_metadata=True,
            )
            sources.append(source)
        elif source_config["kind"] == "sharepoint":
            try:
                import pathway.xpacks.connectors.sharepoint as io_sp

                source = io_sp.read(**source_config["config"], with_metadata=True)
                sources.append(source)
            except ImportError:
                print(
                    "The Pathway Sharepoint connector is part of the commercial offering, "
                    "please contact us for a commercial license."
                )
                sys.exit(1)

    return sources


@click.command()
@click.option("--config_file", default="config.yaml", help="Config file to be used.")
def run(
    config_file: str = "config.yaml",
):
    with open(config_file) as config_f:
        configuration = yaml.safe_load(config_f)

    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key is None:
        print(
            "Please set OPENAI_API_KEY either as a configuration variable, or in the .env file"
        )
        sys.exit(1)

    sources = data_sources(configuration["sources"])

    chat = llms.OpenAIChat(
        model="gpt-4o",
        retry_strategy=ExponentialBackoffRetryStrategy(max_retries=6),
        cache_strategy=DiskCache(),
        temperature=0.0,
    )

    parser = OpenParse()
    embedder = embedders.OpenAIEmbedder(cache_strategy=DiskCache())

    doc_store = VectorStoreServer(
        *sources,
        embedder=embedder,
        splitter=None,  # OpenParse parser handles the chunking
        parser=parser,
    )

    app = BaseRAGQuestionAnswerer(
        llm=chat,
        indexer=doc_store,
        search_topk=6,
        short_prompt_template=prompts.prompt_qa,
    )

    host_config = configuration["host_config"]
    host, port = host_config["host"], host_config["port"]
    app.build_server(host=host, port=port)

    app.run_server(with_cache=True, terminate_on_error=False)


if __name__ == "__main__":
    run()
