import pathway as pw
from llm_app.config import Config
from llm_app.model_wrappers import HFFeatureExtractionTask, HFTextGenerationTask
from pathway.stdlib.ml.index import KNNIndex


class DocumentInputSchema(pw.Schema):
    doc: str


class QueryInputSchema(pw.Schema):
    query: str
    user: str


# EMBEDDER_LOCATOR = "intfloat/e5-large-v2"
# EMBEDDING_DIMENSION = 1024
# MODEL_LOCATOR = "gpt2"


def run(config: Config):
    embedder = HFFeatureExtractionTask(model=config.embedder_locator)

    documents = pw.io.jsonlines.read(
        "./data/pathway-docs-small/",
        schema=DocumentInputSchema,
        mode="streaming",
        autocommit_duration_ms=50,
    )

    enriched_documents = documents + documents.select(
        data=embedder.apply(text=pw.this.doc)
    )

    index = KNNIndex(enriched_documents, d=config.embedding_dimension)

    query, response_writer = pw.io.http.rest_connector(
        host=config.rest_host,
        port=config.rest_port,
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

    model = HFTextGenerationTask(model=config.model_locator)

    responses = prompt.select(
        query_id=pw.this.id,
        result=model.apply(
            pw.this.prompt, return_full_text=False, max_new_tokens=config.max_tokens
        ),
    )

    response_writer(responses)

    pw.run()
