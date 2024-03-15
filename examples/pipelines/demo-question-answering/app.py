import json
import sys
from enum import Enum

import click
import pathway as pw
import pathway.io.fs as io_fs
import pathway.io.gdrive as io_gdrive
import yaml
from dotenv import load_dotenv
from pathway.internals.udfs import DiskCache, ExponentialBackoffRetryStrategy
from pathway.xpacks.llm import embedders, llms, prompts
from pathway.xpacks.llm.parsers import ParseUnstructured
from pathway.xpacks.llm.splitters import TokenCountSplitter
from pathway.xpacks.llm.vector_store import VectorStoreServer

load_dotenv()


class AIResponseType(Enum):
    SHORT = "short"
    LONG = "long"


def _unwrap_udf(func):
    if isinstance(func, pw.UDF):
        return func.__wrapped__
    return func


@pw.udf
def prep_rag_prompt(
    prompt: str, docs: list[pw.Json], filter: str | None, response_type: str
) -> str:
    if filter is None:
        return prompt

    docs = docs.value  # type: ignore

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
def prompt_aggregate(question: str, answers: list[str]) -> str:
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


def data_sources(source_configs) -> list[pw.Table]:
    sources = []
    for source_config in source_configs:
        if source_config["kind"] == "local":
            source = io_fs.read(
                **source_config["config"],
                format="binary",
                with_metadata=True,
            )
            sources.append(source)
        elif source_config["kind"] == "gdrive":
            source = io_gdrive.read(
                **source_config["config"],
                with_metadata=True,
            )
            sources.append(source)
        elif source_config["kind"] == "sharepoint":
            try:
                import pathway.xpacks.connectors.sharepoint as io_sp

                source = io_sp.read(**source_config["config"], with_metadata=True)
                sources.append(source)
            except ImportError:
                print(
                    "The Pathway Sharepoint connector is part of the commercial offering, "
                    "please contact us for a commercial license."
                )
                sys.exit(1)

    return sources


class PathwayRAG:
    class PWAIQuerySchema(pw.Schema):
        prompt: str
        filters: str | None = pw.column_definition(default_value=None)
        model: str | None = pw.column_definition(default_value="gpt-3.5-turbo")
        response_type: str = pw.column_definition(default_value="short")  # short | long

    class SummarizeQuerySchema(pw.Schema):
        text_list: list[str]
        model: str | None = pw.column_definition(default_value="gpt-3.5-turbo")

    class AggregateQuerySchema(pw.Schema):
        question: str
        answers: list[str]
        model: str | None = pw.column_definition(default_value="gpt-3.5-turbo")

    def __init__(
        self,
        *docs: pw.Table,
        llm: pw.UDF,
        embedder: pw.UDF,
        splitter: pw.UDF,
        parser: pw.UDF = ParseUnstructured(),
        doc_post_processors=None,
    ) -> None:
        self.llm = llm

        self.embedder = embedder

        self.vector_server = VectorStoreServer(
            *docs,
            embedder=embedder,
            splitter=splitter,
            parser=parser,
            doc_post_processors=doc_post_processors,
        )

    @pw.table_transformer
    def pw_ai_query(self, pw_ai_queries: pw.Table[PWAIQuerySchema]) -> pw.Table:
        """Main function for RAG applications that answer questions
        based on available information."""

        pw_ai_results = pw_ai_queries + self.vector_server.retrieve_query(
            pw_ai_queries.select(
                metadata_filter=pw.this.filters,
                filepath_globpattern=pw.cast(str | None, None),
                query=pw.this.prompt,
                k=6,
            )
        ).select(
            docs=pw.this.result,
        )

        pw_ai_results += pw_ai_results.select(
            rag_prompt=prep_rag_prompt(
                pw.this.prompt, pw.this.docs, pw.this.filters, pw.this.response_type
            )
        )
        pw_ai_results += pw_ai_results.select(
            result=self.llm(
                llms.prompt_chat_single_qa(pw.this.rag_prompt),
                model=pw.this.model,
            )
        )
        return pw_ai_results

    @pw.table_transformer
    def summarize_query(
        self, summarize_queries: pw.Table[SummarizeQuerySchema]
    ) -> pw.Table:
        summarize_results = summarize_queries.select(
            pw.this.model,
            prompt=prompts.prompt_summarize(pw.this.text_list),
        )
        summarize_results += summarize_results.select(
            result=self.llm(
                llms.prompt_chat_single_qa(pw.this.prompt),
                model=pw.this.model,
            )
        )
        return summarize_results

    @pw.table_transformer
    def aggregate_query(
        self, aggregate_queries: pw.Table[AggregateQuerySchema]
    ) -> pw.Table:
        aggregate_results = aggregate_queries.select(
            pw.this.model,
            prompt=prompt_aggregate(pw.this.question, pw.this.answers),
        )
        aggregate_results += aggregate_results.select(
            result=self.llm(
                llms.prompt_chat_single_qa(pw.this.prompt),
                model=pw.this.model,
            )
        )
        return aggregate_results

    def build_server(self, host: str, port: int) -> None:
        """Adds HTTP connectors to input tables"""

        webserver = pw.io.http.PathwayWebserver(host=host, port=port)

        # connect http endpoint to output writer
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
            "/v1/retrieve",
            self.vector_server.RetrieveQuerySchema,
            self.vector_server.retrieve_query,
        )
        serve(
            "/v1/statistics",
            self.vector_server.StatisticsQuerySchema,
            self.vector_server.statistics_query,
        )
        serve(
            "/v1/pw_list_documents",
            self.vector_server.InputsQuerySchema,
            self.vector_server.inputs_query,
        )
        serve("/v1/pw_ai_answer", self.PWAIQuerySchema, self.pw_ai_query)
        serve(
            "/v1/pw_ai_summary",
            self.SummarizeQuerySchema,
            self.summarize_query,
        )
        serve(
            "/v1/pw_ai_aggregate_responses",
            self.AggregateQuerySchema,
            self.aggregate_query,
        )


@click.command()
@click.option("--config_file", default="config.yaml", help="Config file to be used.")
def run(
    config_file: str = "config.yaml",
):
    with open(config_file) as config_f:
        configuration = yaml.safe_load(config_f)

    GPT_MODEL = configuration["llm_config"]["model"]

    embedder = embedders.OpenAIEmbedder(
        model="text-embedding-ada-002",
        cache_strategy=DiskCache(),
    )

    text_splitter = TokenCountSplitter(max_tokens=400)

    chat = llms.OpenAIChat(
        model=GPT_MODEL,
        retry_strategy=ExponentialBackoffRetryStrategy(max_retries=6),
        cache_strategy=DiskCache(),
        temperature=0.05,
    )

    host_config = configuration["host_config"]
    host, port = host_config["host"], host_config["port"]

    rag_app = PathwayRAG(
        *data_sources(configuration["sources"]),
        embedder=embedder,
        llm=chat,
        splitter=text_splitter,
    )

    rag_app.build_server(host=host, port=port)

    if configuration["cache_options"].get("with_cache", True):
        print("Running with cache enabled.")
        cache_backend = pw.persistence.Backend.filesystem(
            configuration["cache_options"].get("cache_folder", "./Cache")
        )
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
    run()
