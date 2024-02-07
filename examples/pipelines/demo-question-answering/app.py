import json
from enum import Enum

import pathway as pw
from dotenv import load_dotenv
from pathway.internals.asynchronous import DiskCache, ExponentialBackoffRetryStrategy
from pathway.xpacks.llm import embedders, llms, prompts
from pathway.xpacks.llm.parsers import ParseUnstructured
from pathway.xpacks.llm.splitters import TokenCountSplitter
from pathway.xpacks.llm.vector_store import VectorStoreServer


class AIResponseType(Enum):
    SHORT = "short"
    LONG = "long"


load_dotenv()

embedder = embedders.OpenAIEmbedder(
    model="text-embedding-ada-002",
    cache_strategy=DiskCache(),
)

host = "0.0.0.0"
port = 8000

data_sources = []

folder = pw.io.fs.read(
    "data",
    format="binary",
    mode="streaming",
    with_metadata=True,
)

data_sources.append(folder)

# drive_folder = pw.io.gdrive.read(
#     object_id="YOUR FOLDER ID",
#     with_metadata=True,
#     service_user_credentials_file="secret.json",
#     refresh_interval=30,
# )

# data_sources.append(drive_folder)


text_splitter = TokenCountSplitter(max_tokens=400)


vector_server = VectorStoreServer(
    *data_sources,
    embedder=embedder,
    splitter=text_splitter,
    parser=ParseUnstructured(),
)


chat = llms.OpenAIChat(
    model="gpt-3.5-turbo",
    retry_strategy=ExponentialBackoffRetryStrategy(max_retries=6),
    cache_strategy=DiskCache(),
    temperature=0.05,
)


class PWAIQuery(pw.Schema):
    prompt: str
    filters: str | None = pw.column_definition(default_value=None)
    model: str | None = pw.column_definition(default_value="gpt-3.5-turbo")
    response_type: str = pw.column_definition(default_value="short")  # short | long
    openai_api_key: str


pw_ai_endpoint = "/pw_ai_answer"


class SummarizeQuery(pw.Schema):
    text_list: list[str]
    model: str | None = pw.column_definition(default_value="gpt-3.5-turbo")
    openai_api_key: str


summarize_endpoint = "/pw_ai_summary"


class AggregateQuery(pw.Schema):
    question: str
    answers: list[str]
    model: str | None = pw.column_definition(default_value="gpt-3.5-turbo")
    openai_api_key: str


aggregate_endpoint = "/pw_ai_aggregate_responses"


def _unwrap_udf(func):
    if isinstance(func, pw.UDF):
        return func.__wrapped__
    return func


@pw.udf
def gpt_respond(prompt, docs, filter, response_type) -> str:
    if filter is None:
        return prompt

    docs = docs.value

    try:
        docs = [{"text": doc["text"], "path": doc["metadata"]["path"]} for doc in docs]

    except Exception:
        print("No context was found.")

    if response_type == AIResponseType.SHORT.value:
        prompt_func = _unwrap_udf(prompts.prompt_short_qa)
    else:
        prompt_func = _unwrap_udf(prompts.prompt_citing_qa)
    return prompt_func(prompt, docs)


@pw.udf
def prompt_aggregate(question, answers):
    summary_data = "\n".join(answers)

    summaries_str = json.dumps(summary_data, indent=2)

    prompt = f"""Given a json with client names and responses
    to the question: "{question}".
    Categorize clients stance according to their policy and list them separately.
    Use the question and answers to separate them with good logic according to question.
    Use Markdown formatting starting with header level 2 (##).

    Company Policies: ```{summaries_str}```
    Answer:"""

    return prompt


def run(
    with_cache: bool = True,
    cache_backend: pw.persistence.Backend
    | None = pw.persistence.Backend.filesystem("./Cache"),
):
    webserver = pw.io.http.PathwayWebserver(host=host, port=port)
    # Vectorserver

    def serve(route, schema, handler):
        queries, writer = pw.io.http.rest_connector(
            webserver=webserver,
            route=route,
            schema=schema,
            autocommit_duration_ms=50,
            delete_completed_queries=True,
        )
        writer(handler(queries))

    serve(
        "/v1/retrieve", vector_server.RetrieveQuerySchema, vector_server.retrieve_query
    )
    serve(
        "/v1/statistics",
        vector_server.StatisticsQuerySchema,
        vector_server.statistics_query,
    )
    serve(
        "/pw_list_documents",
        vector_server.InputsQuerySchema,
        vector_server.inputs_query,
    )

    gpt_queries, gpt_response_writer = pw.io.http.rest_connector(
        webserver=webserver,
        route=pw_ai_endpoint,
        schema=PWAIQuery,
        autocommit_duration_ms=50,
        delete_completed_queries=True,
    )

    gpt_results = gpt_queries + vector_server.retrieve_query(
        gpt_queries.select(
            metadata_filter=pw.this.filters,
            filepath_globpattern=pw.cast(str | None, None),
            query=pw.this.prompt,
            k=6,
        )
    ).select(
        docs=pw.this.result,
    )

    gpt_results += gpt_results.select(
        rag_prompt=gpt_respond(
            pw.this.prompt, pw.this.docs, pw.this.filters, pw.this.response_type
        )
    )
    gpt_results += gpt_results.select(
        result=chat(
            llms.prompt_chat_single_qa(pw.this.rag_prompt),
            model=pw.this.model,
            api_key=pw.this.openai_api_key,
        )
    )

    summarize_queries, summarize_response_writer = pw.io.http.rest_connector(
        webserver=webserver,
        route=summarize_endpoint,
        schema=SummarizeQuery,
        autocommit_duration_ms=50,
        delete_completed_queries=True,
    )

    summarize_results = summarize_queries.select(
        pw.this.model,
        pw.this.openai_api_key,
        prompt=prompts.prompt_summarize(pw.this.text_list),
    )
    summarize_results += summarize_results.select(
        result=chat(
            llms.prompt_chat_single_qa(pw.this.prompt),
            model=pw.this.model,
            api_key=pw.this.openai_api_key,
        )
    )

    aggregate_queries, aggregate_response_writer = pw.io.http.rest_connector(
        webserver=webserver,
        route=aggregate_endpoint,
        schema=AggregateQuery,
        autocommit_duration_ms=50,
        delete_completed_queries=True,
    )

    aggregate_results = aggregate_queries.select(
        pw.this.model,
        pw.this.openai_api_key,
        prompt=prompt_aggregate(pw.this.question, pw.this.answers),
    )
    aggregate_results += aggregate_results.select(
        result=chat(
            llms.prompt_chat_single_qa(pw.this.prompt),
            model=pw.this.model,
            api_key=pw.this.openai_api_key,
        )
    )

    gpt_response_writer(gpt_results)
    summarize_response_writer(summarize_results)
    aggregate_response_writer(aggregate_results)

    if with_cache:
        if cache_backend is None:
            raise ValueError("Cache usage was requested but the backend is unspecified")
        persistence_config = pw.persistence.Config.simple_config(
            cache_backend,
            persistence_mode=pw.PersistenceMode.UDF_CACHING,
        )
    else:
        persistence_config = None

    pw.run(
        monitoring_level=pw.MonitoringLevel.NONE,
        persistence_config=persistence_config,
    )


if __name__ == "__main__":
    run(with_cache=True)
