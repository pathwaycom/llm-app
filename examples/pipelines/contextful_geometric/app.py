"""
Microservice for a context-aware ChatGPT assistant.

The following program reads in a collection of documents,
embeds each document using the OpenAI document embedding model,
then builds an index for fast retrieval of documents relevant to a question,
effectively replacing a vector database.

The program then starts a REST API endpoint serving queries about programming in Pathway.

Each query text is first turned into a vector using OpenAI embedding service,
then relevant documentation pages are found using a Nearest Neighbor index computed
for documents in the corpus. A prompt is built from the relevant documentations pages
and sent to the OpenAI chat service for processing.

To optimize use of tokens per query, this pipeline asks a question with a small number
of documents embedded in the prompt. If OpenAI chat fails to answer based on these documents,
the number of documents is increased by `factor` given as an argument, and continues to
do so until either question is answered or a limit of iterations is reached.

Please check the README.md in this directory for how-to-run instructions.
"""

import os

import dotenv
import pathway as pw
from pathway.stdlib.indexing import default_vector_document_index
from pathway.xpacks.llm.embedders import OpenAIEmbedder
from pathway.xpacks.llm.llms import OpenAIChat
from pathway.xpacks.llm.question_answering import (
    answer_with_geometric_rag_strategy_from_index,
)

# To use advanced features with Pathway Scale, get your free license key from
# https://pathway.com/features and paste it below.
# To use Pathway Community, comment out the line below.
pw.set_license_key("demo-license-key-with-telemetry")

dotenv.load_dotenv()


class DocumentInputSchema(pw.Schema):
    doc: str


class QueryInputSchema(pw.Schema):
    query: str
    user: str


def run(
    *,
    data_dir: str = os.environ.get("PATHWAY_DATA_DIR", "./data/"),
    api_key: str = os.environ.get("OPENAI_API_KEY", ""),
    host: str = os.environ.get("PATHWAY_REST_CONNECTOR_HOST", "0.0.0.0"),
    port: int = int(os.environ.get("PATHWAY_REST_CONNECTOR_PORT", "8080")),
    embedder_locator: str = "text-embedding-ada-002",
    embedding_dimension: int = 1536,
    model_locator: str = "gpt-3.5-turbo",
    max_tokens: int = 60,
    temperature: float = 0.0,
    n_starting_documents: int = 2,
    factor: int = 2,
    max_iterations: int = 4,
    **kwargs,
):
    embedder = OpenAIEmbedder(
        api_key=api_key,
        model=embedder_locator,
        retry_strategy=pw.udfs.FixedDelayRetryStrategy(),
        cache_strategy=pw.udfs.DefaultCache(),
    )

    documents = pw.io.jsonlines.read(
        data_dir,
        schema=DocumentInputSchema,
        mode="streaming",
        autocommit_duration_ms=50,
    )

    index = default_vector_document_index(
        data_column=documents.doc,
        data_table=documents,
        dimensions=embedding_dimension,
        embedder=embedder,
    )

    query, response_writer = pw.io.http.rest_connector(
        host=host,
        port=port,
        schema=QueryInputSchema,
        autocommit_duration_ms=50,
        delete_completed_queries=True,
    )

    model = OpenAIChat(
        api_key=api_key,
        model=model_locator,
        temperature=temperature,
        max_tokens=max_tokens,
        retry_strategy=pw.udfs.FixedDelayRetryStrategy(),
        cache_strategy=pw.udfs.DefaultCache(),
    )

    responses = query.select(
        result=answer_with_geometric_rag_strategy_from_index(
            query.query,
            index,
            documents.doc,
            model,
            n_starting_documents,
            factor,
            max_iterations,
        )
    )

    response_writer(responses)

    pw.run()


if __name__ == "__main__":
    run()
