import os

import pathway as pw
from model_wrappers import APIModel, OpenAIEmbeddingModel
from pathway.stdlib.ml.index import KNNIndex


class DocumentInputSchema(pw.Schema):
    doc: str


class QueryInputSchema(pw.Schema):
    query: str
    user: str


HTTP_HOST = os.environ.get("PATHWAY_REST_CONNECTOR_HOST", "127.0.0.1")
HTTP_PORT = os.environ.get("PATHWAY_REST_CONNECTOR_PORT", "8080")

MODEL_HTTP_HOST = os.environ.get("MODEL_REST_CONNECTOR_HOST", "127.0.0.1")
MODEL_HTTP_PORT = os.environ.get("MODEL_REST_CONNECTOR_PORT", "8888")

API_KEY = os.environ.get("OPENAI_API_TOKEN")
EMBEDDER_LOCATOR = "text-embedding-ada-002"
EMBEDDING_DIMENSION = 1536

MODEL_LOCATOR = "gpt-3.5-turbo"  # Change to 'gpt-4' if you have access.
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

    model = APIModel(api_base_url=f"http://{MODEL_HTTP_HOST}:{MODEL_HTTP_PORT}")

    responses = prompt.select(
        query_id=pw.this.id,
        result=model.apply(
            pw.this.prompt,
        ),
    )

    response_writer(responses)

    pw.run()
