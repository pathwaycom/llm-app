import os

import pathway as pw
from model_wrappers import HFFeatureExtractionTask, HFTextGenerationTask
from pathway.stdlib.ml.index import KNNIndex


class DocumentInputSchema(pw.Schema):
    doc: str


class QueryInputSchema(pw.Schema):
    query: str
    user: str


HTTP_HOST = os.environ.get("PATHWAY_REST_CONNECTOR_HOST", "127.0.0.1")
HTTP_PORT = os.environ.get("PATHWAY_REST_CONNECTOR_PORT", "8080")

EMBEDDER_LOCATOR = "intfloat/e5-large-v2"
EMBEDDING_DIMENSION = 1024
MODEL_LOCATOR = "gpt2"


def run():
    embedder = HFFeatureExtractionTask(model=EMBEDDER_LOCATOR)

    documents = pw.io.jsonlines.read(
        "../data/pathway-docs-small/",
        schema=DocumentInputSchema,
        mode="streaming",
        autocommit_duration_ms=50,
    )

    enriched_documents = documents + documents.select(
        data=embedder.apply(text=pw.this.doc)
    )

    index = KNNIndex(enriched_documents, d=EMBEDDING_DIMENSION)

    query, response_writer = pw.io.http.rest_connector(
        host=HTTP_HOST,
        port=int(HTTP_PORT),
        schema=QueryInputSchema,
        autocommit_duration_ms=50,
    )

    query += query.select(
        data=embedder.apply(text=pw.this.query),
    )

    query_context = index.query(query, k=1).select(
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

    model = HFTextGenerationTask(model=MODEL_LOCATOR)

    responses = prompt.select(
        query_id=pw.this.id,
        result=model.apply(pw.this.prompt, return_full_text=False, max_new_tokens=60),
    )

    response_writer(responses)

    pw.run()
