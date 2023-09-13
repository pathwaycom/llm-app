"""
Microservice for  a context-aware ChatGPT assistant.

The following program reads in a collection of documents,
embeds each document using the OpenAI document embedding model,
then builds an index for fast retrieval of documents relevant to a question,
effectively replacing a vector database.

The program then starts a REST API endpoint serving queries about programming in Pathway.

Each query text is first turned into a vector using OpenAI embedding service,
then relevant documentation pages are found using a Nearest Neighbor index computed
for documents in the corpus. A prompt is build from the relevant documentations pages
and sent to the OpenAI GPT-4 chat service for processing.

Usage:
In the root of this repository run:
`poetry run ./run_examples.py contextful`
or, if all dependencies are managed manually rather than using poetry
`python examples/pipelines/contextful/app.py`

You can also run this example directly in the environment with llm_app instaslled.

To call the REST API:
curl --data '{"user": "user", "query": "How to connect to Kafka in Pathway?"}' http://localhost:8080/ | jq
"""

import os

import pathway as pw
from pathway.stdlib.ml.index import KNNIndex

from llm_app.model_wrappers import OpenAIChatGPTModel, OpenAIEmbeddingModel


class DocumentInputSchema(pw.Schema):
    doc: str


class QueryInputSchema(pw.Schema):
    query: str
    user: str


def run(
    *,
    data_dir: str = os.environ.get("PATHWAY_DATA_DIR", "./examples/data/pathway-docs/"),
    api_key: str = os.environ.get("OPENAI_API_TOKEN", ""),
    host: str = "0.0.0.0",
    port: int = 8080,
    embedder_locator: str = "text-embedding-ada-002",
    embedding_dimension: int = 1536,
    model_locator: str = "gpt-3.5-turbo",
    max_tokens: int = 60,
    temperature: float = 0.0,
    **kwargs,
):
    embedder = OpenAIEmbeddingModel(api_key=api_key)

    documents = pw.io.jsonlines.read(
        data_dir,
        schema=DocumentInputSchema,
        mode="streaming",
        autocommit_duration_ms=50,
    )

    enriched_documents = documents + documents.select(
        vector=embedder.apply(text=pw.this.doc, locator=embedder_locator)
    )

    index = KNNIndex(
        enriched_documents.vector, enriched_documents, n_dimensions=embedding_dimension
    )

    query, response_writer = pw.io.http.rest_connector(
        host=host,
        port=port,
        schema=QueryInputSchema,
        autocommit_duration_ms=50,
    )

    query += query.select(
        vector=embedder.apply(text=pw.this.query, locator=embedder_locator),
    )

    query_context = query + index.get_nearest_items(
        query.vector, k=3, collapse_rows=True
    ).select(documents_list=pw.this.doc).promise_universe_is_equal_to(query)

    @pw.udf
    def build_prompt(documents, query):
        docs_str = "\n".join(documents)
        prompt = f"Given the following documents : \n {docs_str} \nanswer this query: {query}"
        return prompt

    prompt = query_context.select(
        prompt=build_prompt(pw.this.documents_list, pw.this.query)
    )

    model = OpenAIChatGPTModel(api_key=api_key)

    responses = prompt.select(
        query_id=pw.this.id,
        result=model.apply(
            pw.this.prompt,
            locator=model_locator,
            temperature=temperature,
            max_tokens=max_tokens,
        ),
    )

    response_writer(responses)

    pw.run()


if __name__ == "__main__":
    run()
