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
In llm_app/ run:
python main.py --mode contextful

To call the REST API:
curl --data '{"user": "user", "query": "How to connect to Kafka in Pathway?"}' http://localhost:8080/ | jq
"""
import os

import pathway as pw
from model_wrappers import OpenAIChatGPTModel, OpenAIEmbeddingModel
from pathway.stdlib.ml.index import KNNIndex


class DocumentInputSchema(pw.Schema):
    doc: str


class QueryInputSchema(pw.Schema):
    query: str
    user: str


HTTP_HOST = os.environ.get("PATHWAY_REST_CONNECTOR_HOST", "127.0.0.1")
HTTP_PORT = os.environ.get("PATHWAY_REST_CONNECTOR_PORT", "8080")

API_KEY = os.environ.get("OPENAI_API_TOKEN")
EMBEDDER_LOCATOR = "text-embedding-ada-002"
EMBEDDING_DIMENSION = 1536

MODEL_LOCATOR = "gpt-3.5-turbo" #  Change to 'gpt-4' if you have access.
TEMPERATURE = 0.0
MAX_TOKENS = 60


def run():
    embedder = OpenAIEmbeddingModel(api_key=API_KEY)

    documents = pw.io.jsonlines.read(
        "../data/pathway-docs/",
        schema=DocumentInputSchema,
        mode="streaming",
        autocommit_duration_ms=50,
    )

    enriched_documents = documents + documents.select(
        data=embedder.apply(text=pw.this.doc, locator=EMBEDDER_LOCATOR)
    )

    index = KNNIndex(enriched_documents, d=EMBEDDING_DIMENSION)

    query, response_writer = pw.io.http.rest_connector(
        host=HTTP_HOST,
        port=int(HTTP_PORT),
        schema=QueryInputSchema,
        autocommit_duration_ms=50,
    )

    query += query.select(
        data=embedder.apply(text=pw.this.query, locator=EMBEDDER_LOCATOR),
    )

    query_context = index.query(query, k=3).select(
        pw.this.query, documents_list=pw.this.result
    )

    @pw.udf
    def build_prompt(documents, query):
        docs_str = "\n".join(documents)
        prompt = f"Given the following documents : \n {docs_str} \nanswer this query: {query}"
        return prompt

    prompt = query_context.select(
        prompt=build_prompt(pw.this.documents_list, pw.this.query)
    )

    model = OpenAIChatGPTModel(api_key=API_KEY)

    responses = prompt.select(
        query_id=pw.this.id,
        result=model.apply(
            pw.this.prompt,
            locator=MODEL_LOCATOR,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        ),
    )

    response_writer(responses)

    pw.run()
