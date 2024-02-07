import argparse
import os

from pathway.xpacks.llm.embedders import OpenAIEmbedder
from pathway.xpacks.llm.parsers import ParseUnstructured
from pathway.xpacks.llm.splitters import TokenCountSplitter
from pathway.xpacks.llm.vector_store import VectorStoreServer
from sources.gdrive import get_table as get_gdrive_table
from sources.local import get_table as get_local_table
from sources.sharepoint import get_table as get_sharepoint_table


def data_sources(source_types):
    parsed_source_types = set([x.strip().lower() for x in source_types.split(",")])
    sources = []
    if "local" in parsed_source_types:
        sources.append(get_local_table())
    if "sharepoint" in parsed_source_types:
        sources.append(get_sharepoint_table())
    if "gdrive" in parsed_source_types:
        sources.append(get_gdrive_table())
    return sources


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Pathway realtime document indexing demo",
        description="""
        This is the demo of real-time indexing of the documents from various data sources.
        It runs a simple web server that is capable of answering queries on the endpoints
        /v1/retrieve, /v1/statistics, /v1/inputs. Please refer to the "Test the REST endpoint"
        section at Hosted Pipelines website: https://cloud.pathway.com.

        Currently, it supports several data sources: the local one, Google Drive, and Microsoft SharePoint.

        For the demo, you need to store your Open AI key in the OPENAI_API_KEY environment variable.
        """,
    )
    parser.add_argument(
        "--host",
        help="Host that will be used for running the web server",
        default="0.0.0.0",
    )
    parser.add_argument(
        "--port",
        help="Port that will be used by the web server",
        type=int,
        default=21401,
    )
    parser.add_argument(
        "--source-types",
        help="Comma-separated source types to be used. "
        "Possible options are local, gdrive, sharepoint. If the local "
        "source is chosen, it will read documents from the top level of "
        "the 'files-for-indexing/' folder",
        default="local",
    )
    args = parser.parse_args()

    splitter = TokenCountSplitter(max_tokens=1000)
    embedder = OpenAIEmbedder(api_key=os.environ["OPENAI_API_KEY"])
    parser = ParseUnstructured()
    vs_server = VectorStoreServer(
        *data_sources(args.source_types),
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
