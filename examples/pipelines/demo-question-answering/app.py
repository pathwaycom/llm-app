import logging
import sys

import click
import pathway as pw
import yaml
from dotenv import load_dotenv
from pathway.udfs import DiskCache, ExponentialBackoffRetryStrategy
from pathway.xpacks.llm import embedders, llms, parsers, splitters
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from pathway.xpacks.llm.vector_store import VectorStoreServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

load_dotenv()


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

    GPT_MODEL = configuration["llm_config"]["model"]

    embedder = embedders.OpenAIEmbedder(
        model="text-embedding-ada-002",
        cache_strategy=DiskCache(),
    )

    chat = llms.OpenAIChat(
        model=GPT_MODEL,
        retry_strategy=ExponentialBackoffRetryStrategy(max_retries=6),
        cache_strategy=DiskCache(),
        temperature=0.05,
    )

    host_config = configuration["host_config"]
    host, port = host_config["host"], host_config["port"]

    doc_store = VectorStoreServer(
        *data_sources(configuration["sources"]),
        embedder=embedder,
        splitter=splitters.TokenCountSplitter(max_tokens=400),
        parser=parsers.ParseUnstructured(),
    )

    rag_app = BaseRAGQuestionAnswerer(llm=chat, indexer=doc_store)

    rag_app.build_server(host=host, port=port)

    rag_app.run_server(with_cache=True, terminate_on_error=False)


if __name__ == "__main__":
    run()
