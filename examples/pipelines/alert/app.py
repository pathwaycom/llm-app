"""
Microservice for a context-aware alerting ChatGPT assistant.

This demo is very similar to `contextful` example with an additional real time alerting capability.
For the demo, alerts are sent to the Slack (you need `slack_alert_channel_id` and `slack_alert_token`), you can
either put these env variables in .env file under llm-app directory,
or create env variables in terminal (ie. export in bash)
If you don't have Slack, you can leave them empty and app will print the notifications to standard output instead.

Upon starting, a REST API endpoint is opened by the app to serve queries about input folder `data_dir`.

We can create notifications by sending query to API stating we want to be modified.
Alternatively, the provided Streamlit chat app can be used.
One example would be `Tell me and alert about start date of campaign for Magic Cola`

How It Works?

Each query text is first turned into a vector using OpenAI embedding service,
then relevant documentation pages are found using a Nearest Neighbor index computed
for documents in the corpus. A prompt is build from the relevant documentations pages
and sent to the OpenAI GPT3.5 chat service for processing and answering.

Once you run, Pathway looks for any changes in data sources, and efficiently detects changes to the relevant documents.
When a change of source documents is detected, the LLM is asked to answer the query again,
and if the new answer is sufficiently different, a notification is created.

Usage:
In the root of this repository run:
`poetry run ./run_examples.py alerts`
or, if all dependencies are managed manually rather than using poetry
You can either
`python examples/pipelines/alerts/app.py`
or
`python ./run_examples.py alert`

You can also run this example directly in the environment with llm_app installed.

To create alerts:
You can call the REST API:
curl --data '{"user": "user", "query": "How to connect to Kafka in Pathway?"}' http://localhost:8080/ | jq
Or start streamlit UI:
First go to examples/ui directory with `cd llm-app/examples/ui/`
run `streamlit run server.py`
"""

import os

import pathway as pw
from pathway.stdlib.ml.index import KNNIndex

from examples.example_utils import find_last_modified_file, get_file_info
from llm_app import deduplicate, send_slack_alerts
from llm_app.model_wrappers import OpenAIChatGPTModel, OpenAIEmbeddingModel


class DocumentInputSchema(pw.Schema):
    doc: str


class QueryInputSchema(pw.Schema):
    query: str
    user: str


# Helper Functions
@pw.udf
def build_prompt(documents, query):
    docs_str = "\n".join(
        [f"Doc-({idx}) -> {doc}" for idx, doc in enumerate(documents[::-1])]
    )
    prompt = f"""Given a set of documents, answer user query. If answer is not in docs, say it can't be inferred.

Docs: {docs_str}
Query: '{query}'
Final Response:"""
    return prompt


@pw.udf
def build_prompt_check_for_alert_request_and_extract_query(query: str) -> str:
    prompt = f"""Evaluate the user's query and identify if there is a request for notifications on answer alterations:
    User Query: '{query}'

    Respond with 'Yes' if there is a request for alerts, and 'No' if not,
    followed by the query without the alerting request part.

    Examples:
    "Tell me about windows in Pathway" => "No. Tell me about windows in Pathway"
    "Tell me and alert about windows in Pathway" => "Yes. Tell me about windows in Pathway"
    """
    return prompt


@pw.udf
def split_answer(answer: str) -> tuple[bool, str]:
    alert_enabled = "yes" in answer[:3].lower()
    true_query = answer[3:].strip(' ."')
    return alert_enabled, true_query


def build_prompt_compare_answers(new: str, old: str) -> str:
    prompt = f"""
    Are the two following responses deviating?
    Answer with Yes or No.

    First response: "{old}"

    Second response: "{new}"
    """
    return prompt


def make_query_id(user, query) -> str:
    return str(hash(query + user))  # + str(time.time())


@pw.udf
def construct_notification_message(query: str, response: str, metainfo=None) -> str:
    return f'New response for question "{query}":\n{response}\n{str(metainfo)}'


@pw.udf
def construct_message(response, alert_flag, metainfo=None):
    if alert_flag:
        if metainfo:
            response += "\n" + str(metainfo)
        return response + "\n\n🔔 Activated"
    return response


def decision_to_bool(decision: str) -> bool:
    return "yes" in decision.lower()


@pw.udf
def add_meta_info(file_path) -> dict:
    fname = find_last_modified_file(file_path)
    info_dict = get_file_info(fname)
    return f"""\nBased on file: {info_dict['File']} modified by {info_dict['Owner']} on {info_dict['Last Edit']}."""


def run(
    *,
    data_dir: str = os.environ.get(
        "PATHWAY_DATA_DIR", "./examples/data/magic-cola/live/"
    ),
    api_key: str = os.environ.get("OPENAI_API_KEY", ""),
    host: str = "0.0.0.0",
    port: int = 8080,
    embedder_locator: str = "text-embedding-ada-002",
    embedding_dimension: int = 1536,
    model_locator: str = "gpt-3.5-turbo",
    max_tokens: int = 400,
    temperature: float = 0.0,
    slack_alert_channel_id=os.environ.get("SLACK_ALERT_CHANNEL_ID", ""),
    slack_alert_token=os.environ.get("SLACK_ALERT_TOKEN", ""),
    **kwargs,
):
    # Part I: Build index
    embedder = OpenAIEmbeddingModel(api_key=api_key)

    documents = pw.io.jsonlines.read(
        data_dir,
        schema=DocumentInputSchema,
        mode="streaming_with_deletions",
        autocommit_duration_ms=50,
    )

    enriched_documents = documents + documents.select(
        data=embedder.apply(text=pw.this.doc, locator=embedder_locator)
    )

    index = KNNIndex(
        enriched_documents.data, enriched_documents, n_dimensions=embedding_dimension
    )

    # Part II: receive queries, detect intent and prepare cleaned query

    query, response_writer = pw.io.http.rest_connector(
        host=host,
        port=port,
        schema=QueryInputSchema,
        autocommit_duration_ms=50,
    )

    model = OpenAIChatGPTModel(api_key=api_key)

    query += query.select(
        prompt=build_prompt_check_for_alert_request_and_extract_query(query.query)
    )
    query += query.select(
        tupled=split_answer(
            model.apply(
                pw.this.prompt,
                locator=model_locator,
                temperature=temperature,
                max_tokens=100,
            )
        ),
    )
    query = query.select(
        pw.this.user,
        alert_enabled=pw.this.tupled[0],
        query=pw.this.tupled[1],
    )

    query += query.select(
        data=embedder.apply(text=pw.this.query, locator=embedder_locator),
        query_id=pw.apply(make_query_id, pw.this.user, pw.this.query),
    )

    # Part III: respond to queries

    query_context = query + index.get_nearest_items(query.data, k=3).select(
        documents_list=pw.this.doc
    ).with_universe_of(query)

    prompt = query_context.select(
        pw.this.query_id,
        pw.this.query,
        pw.this.alert_enabled,
        prompt=build_prompt(pw.this.documents_list, pw.this.query),
    )

    responses = prompt.select(
        pw.this.query_id,
        pw.this.query,
        pw.this.alert_enabled,
        response=model.apply(
            pw.this.prompt,
            locator=model_locator,
            temperature=temperature,
            max_tokens=max_tokens,
        ),
    )

    output = responses.select(
        result=construct_message(pw.this.response, pw.this.alert_enabled)
    )

    response_writer(output)

    # Part IV: send alerts about responses which changed significantly.

    responses = responses.filter(pw.this.alert_enabled)

    def acceptor(new: str, old: str) -> bool:
        if new == old:
            return False

        decision = model(
            build_prompt_compare_answers(new, old),
            locator=model_locator,
            max_tokens=20,
        )

        return decision_to_bool(decision)

    deduplicated_responses = deduplicate(
        responses,
        col=responses.response,
        acceptor=acceptor,
        instance=responses.query_id,
    )

    alerts = deduplicated_responses.select(
        message=construct_notification_message(
            pw.this.query, pw.this.response, add_meta_info(data_dir)
        )
    )

    send_slack_alerts(alerts.message, slack_alert_channel_id, slack_alert_token)

    pw.run()


if __name__ == "__main__":
    run()
