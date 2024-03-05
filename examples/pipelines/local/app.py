"""
Microservice for a privacy preserving LLM assistant.

The following program reads in a collection of documents from local directory,
embeds each document using a locally deployed SentenceTransformer,
then builds an index for fast retrieval of documents relevant to a question,
effectively replacing a vector database.

The program then starts a REST API endpoint serving queries about programming in Pathway.

Each query text is first turned into a vector using the SentenceTransformer,
then relevant documentation pages are found using a Nearest Neighbor index computed
for documents in the corpus. A prompt is build from the relevant documentations pages
and run through a local LLM downloaded form the HuggingFace repository.

Because of restrictions of model you need to be careful about the length of prompt with
the embedded documents. In this example this is solved with cropping the prompt to a set
length - the query is in the beginning of the prompt, so it won't be removed, but some
parts of documents to be omitted from the query.
Depending on the length of documents and the model you use this may not be necessary or
you can use some more refined method of shortening your prompts.

Usage:
In the root of this repository run:
`poetry run ./run_examples.py local`
or, if all dependencies are managed manually rather than using poetry
`python examples/pipelines/local/app.py`

You can also run this example directly in the environment with llm_app instaslled.

To call the REST API:
curl --data '{"user": "user", "query": "How to connect to Kafka in Pathway?"}' http://localhost:8080/ | jq
"""

import os

import pathway as pw
from pathway.stdlib.ml.index import KNNIndex
from pathway.xpacks.llm.embedders import SentenceTransformerEmbedder
from pathway.xpacks.llm.llms import HFPipelineChat, prompt_chat_single_qa


class DocumentInputSchema(pw.Schema):
    doc: str


class QueryInputSchema(pw.Schema):
    query: str
    user: str


def run(
    *,
    data_dir: str = os.environ.get(
        "PATHWAY_DATA_DIR", "./examples/data/pathway-docs-small/"
    ),
    host: str = "0.0.0.0",
    port: int = 8080,
    model_locator: str = os.environ.get("MODEL", "gpt2"),
    embedder_locator: str = os.environ.get("EMBEDDER", "intfloat/e5-large-v2"),
    max_tokens: int = 60,
    device: str = "cpu",
    **kwargs,
):
    embedder = SentenceTransformerEmbedder(model=embedder_locator, device=device)
    embedding_dimension = len(embedder.__wrapped__(""))

    documents = pw.io.jsonlines.read(
        data_dir,
        schema=DocumentInputSchema,
        mode="streaming",
        autocommit_duration_ms=50,
    )

    enriched_documents = documents + documents.select(vector=embedder(text=pw.this.doc))

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

    query += query.select(
        vector=embedder(text=pw.this.query),
    )

    query_context = query + index.get_nearest_items(
        query.vector, k=3, collapse_rows=True
    ).select(documents_list=pw.this.doc)

    @pw.udf
    def build_prompt(documents, query):
        docs_str = "\n".join(documents)
        prompt = f"You are given a query: {query}\n Answer this query based on the following documents: \n {docs_str}"
        return prompt

    prompt = query_context.select(
        prompt=build_prompt(pw.this.documents_list, pw.this.query)
    )

    model = HFPipelineChat(
        model=model_locator,
        device=device,
        return_full_text=False,
        max_new_tokens=max_tokens,
    )

    # Cropping the prompt so that it is short enough for the model. Depending on input documents
    # and chosen model this may not be necessary.
    prompt = prompt.select(
        prompt=model.crop_to_max_length(
            input_string=pw.this.prompt, max_prompt_length=500
        )
    )

    responses = prompt.select(
        query_id=pw.this.id,
        result=model(prompt_chat_single_qa(pw.this.prompt)),
    )

    response_writer(responses)

    pw.run()


if __name__ == "__main__":
    run()
