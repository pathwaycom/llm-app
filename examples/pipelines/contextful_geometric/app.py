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

To optimise use of tokens per query, this pipeline asks a question with a small number
of documents embedded in the prompt. If OpenAI chat fails to answer based on these documents,
the number of documents is increased by `factor` given as an argument, and continues to
do so until either question is answered or a limit of iterations is reached.

Usage:
In the root of this repository run:
`poetry run ./run_examples.py contextful-geometric`
or, if all dependencies are managed manually rather than using poetry
`python examples/pipelines/contextful_geometric/app.py`

You can also run this example directly in the environment with llm_app installed.

To call the REST API:
curl --data '{"user": "user", "query": "How to connect to Kafka in Pathway?"}' http://localhost:8080/ | jq
"""

import os

import pathway as pw
from pathway.stdlib.ml.index import KNNIndex
from pathway.xpacks.llm.embedders import OpenAIEmbedder
from pathway.xpacks.llm.llms import OpenAIChat
from pathway.xpacks.llm.question_answering import answer_with_geometric_rag_strategy


class DocumentInputSchema(pw.Schema):
    doc: str


class QueryInputSchema(pw.Schema):
    query: str
    user: str


def run(
    *,
    data_dir: str = os.environ.get("PATHWAY_DATA_DIR", "./examples/data/pathway-docs/"),
    api_key: str = os.environ.get("OPENAI_API_KEY", ""),
    host: str = "0.0.0.0",
    port: int = 8080,
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
        retry_strategy=pw.asynchronous.FixedDelayRetryStrategy(),
        cache_strategy=pw.asynchronous.DefaultCache(),
    )

    documents = pw.io.jsonlines.read(
        data_dir,
        schema=DocumentInputSchema,
        mode="streaming",
        autocommit_duration_ms=50,
    )

    enriched_documents = documents + documents.select(vector=embedder(pw.this.doc))

    index = KNNIndex(
        enriched_documents.vector, enriched_documents, n_dimensions=embedding_dimension
    )

    query, response_writer = pw.io.http.rest_connector(
        host=host,
        port=port,
        schema=QueryInputSchema,
        autocommit_duration_ms=50,
        delete_completed_queries=True,
    )

    query += query.select(vector=embedder(pw.this.query))

    max_documents = n_starting_documents * (factor ** (max_iterations - 1))

    query_context = query + index.get_nearest_items(
        query.vector, k=max_documents, collapse_rows=True
    ).select(documents_list=pw.this.doc)

    model = OpenAIChat(
        api_key=api_key,
        model=model_locator,
        temperature=temperature,
        max_tokens=max_tokens,
        retry_strategy=pw.asynchronous.FixedDelayRetryStrategy(),
        cache_strategy=pw.asynchronous.DefaultCache(),
    )

    responses = query_context.select(
        result=answer_with_geometric_rag_strategy(
            query_context.query,
            query_context.documents_list,
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
