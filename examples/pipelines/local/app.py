import pathway as pw
from pathway.stdlib.ml.index import KNNIndex

from llm_app.model_wrappers import HFTextGenerationTask, SentenceTransformerTask


class DocumentInputSchema(pw.Schema):
    doc: str


class QueryInputSchema(pw.Schema):
    query: str
    user: str


def run(
    *,
    host: str = "0.0.0.0",
    port: int = 8080,
    data_dir: str = "./data/pathway-docs-small/",
    model_locator: str = "gpt2",
    embedder_locator: str = "intfloat/e5-large-v2",
    embedding_dimension: int = 1024,
    max_tokens: int = 60,
    **kwargs,
):
    embedder = SentenceTransformerTask(model=embedder_locator)

    documents = pw.io.jsonlines.read(
        data_dir,
        schema=DocumentInputSchema,
        mode="streaming",
        autocommit_duration_ms=50,
    )

    enriched_documents = documents + documents.select(
        data=embedder.apply(text=pw.this.doc)
    )

    index = KNNIndex(enriched_documents, d=embedding_dimension)

    query, response_writer = pw.io.http.rest_connector(
        host=host,
        port=port,
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

    model = HFTextGenerationTask(model=model_locator)

    responses = prompt.select(
        query_id=pw.this.id,
        result=model.apply(
            pw.this.prompt, return_full_text=False, max_new_tokens=max_tokens
        ),
    )

    response_writer(responses)

    pw.run()


if __name__ == "__main__":
    run()
