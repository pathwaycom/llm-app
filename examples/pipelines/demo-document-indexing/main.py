import argparse
import os
import sys

import pathway.io.fs as io_fs
import pathway.io.gdrive as io_gdrive
import yaml
from dotenv import load_dotenv
from pathway.xpacks.llm import embedders, parsers, splitters, vector_store


def data_sources(source_configs):
    sources = []
    for source_config in source_configs:
        if source_config["kind"] == "local":
            source = io_fs.read(
                **source_config["config"],
                format="binary",
                with_metadata=True,
            )
            sources.append(source)
        elif source_config["kind"] == "gdrive":
            source = io_gdrive.read(
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


if __name__ == "__main__":
    load_dotenv()
    argparser = argparse.ArgumentParser(
        prog="Pathway realtime document indexing demo",
        description="""
        This is the demo of real-time indexing of the documents from various data sources.
        It runs a simple web server that is capable of answering queries on the endpoints
        /v1/retrieve, /v1/statistics, /v1/inputs. Please refer to the "Test the REST endpoint"
        section at Hosted Pipelines website: https://cloud.pathway.com.

        Currently, it supports several data sources: the local one, Google Drive, and,
        in a commercial offering, Microsoft SharePoint.

        For the demo, you need to store your Open AI key in the OPENAI_API_KEY environment variable,
        the easiest way is to add it to the .env file.
        """,
    )
    argparser.add_argument(
        "--host",
        help="Host that will be used for running the web server.",
        default="0.0.0.0",
    )
    argparser.add_argument(
        "--port",
        help="Port that will be used by the web server.",
        type=int,
        default=8000,
    )
    argparser.add_argument(
        "--sources-config",
        help="Path to sources configuration file",
        default="sources_configuration.yaml",
    )
    args = argparser.parse_args()
    with open(args.sources_config) as config_f:
        configuration = yaml.safe_load(config_f)

    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key is None:
        print(
            "Please set OPENAI_API_KEY either as a configuration variable, or in the .env file"
        )
        sys.exit(1)

    splitter = splitters.TokenCountSplitter(max_tokens=200)
    embedder = embedders.OpenAIEmbedder(api_key=openai_api_key)
    parser = parsers.ParseUnstructured()
    vs_server = vector_store.VectorStoreServer(
        *data_sources(configuration["sources"]),
        embedder=embedder,
        splitter=splitter,
        parser=parser,
    )
    vs_server.run_server(
        host=args.host,
        port=args.port,
        threaded=False,
        with_cache=True,
    )
