"""
Microservice for a context-aware alerting ChatGPT assistant.

This demo is very similar to `alert` example, only difference is the data source (Google Drive)
For the demo, alerts are sent to Slack (you need to provide `slack_alert_channel_id` and `slack_alert_token`),
you can either put these env variables in .env file under llm-app directory,
or create env variables in terminal (i.e. export in bash)
If you don't have Slack, you can leave them empty and app will print the notifications instead.

The program then starts a REST API endpoint serving queries about Google Docs stored in a
Google Drive folder.

We can create notifications by asking from Streamlit or sending query to API stating we want to be notified.
One example would be `Tell me and alert about start date of campaign for Magic Cola`

How It Works?
First, Pathway connects to Google Drive, extract all documents, split into chunks, turn them into
vectors using OpenAI embedding service, and store in a nearest neighbor index.

Each query text is first turned into a vector, then relevant document chunks are found
using the nearest neighbor index. A prompt is build from the relevant chunk
and sent to the OpenAI GPT3.5 chat service for processing and answering.

After an initial answer is provided, Pathway monitors changes to documents and selectively
re-triggers potentially affected queries. If new answer is significantly different form
the previously presented one, a new notification is created.

Usage:
First, obtain the Google credentials as in the examples/pipelines/drive_alert/README_GDRIVE_AUTH.md

set you env variables in .env file placed in root of repo

```
OPENAI_API_KEY=sk-...
PATHWAY_REST_CONNECTOR_HOST=127.0.0.1
PATHWAY_REST_CONNECTOR_PORT=8181
SLACK_ALERT_CHANNEL_ID=  # if unset, alerts will be printed to terminal
SLACK_ALERT_TOKEN=
FILE_OR_DIRECTORY_ID=  # file or folder id that you want to track that we have retrieved earlier
GOOGLE_CREDS=examples/pipelines/drive_alert/secrets.json  # Default location of Google Drive authorization secrets
```

In the root of this repository run:
`poetry run ./run_examples.py drivealert`
or, if all dependencies are managed manually rather than using poetry
You can either
`python examples/pipelines/drivealert/app.py`
or
`python ./run_examples.py drivealert`

You can also run this example directly in the environment with llm_app installed.

To create alerts:
You can call the REST API:
curl --data '{
  "user": "user",
  "query": "When does the magic cola campaign start? Alert me if the start date changes."
}' http://localhost:8080/ | jq

Or start streamlit UI:
First go to examples/pipelines/drive_alert/ui directory with `cd examples/pipelines/drive_alert/ui/`
run `streamlit run server.py`
"""

import os

import pathway as pw
from pathway.stdlib.ml.index import KNNIndex

from llm_app import chunk_texts, extract_texts, send_slack_alerts
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
    prompt = f"""Given a set of documents, answer user query. If answer is not in docs, say it cant be inferred.

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
    return str(hash(query + user))


@pw.udf
def construct_notification_message(query: str, response: str) -> str:
    return f'New response for question "{query}":\n{response}'


@pw.udf
def construct_message(response, alert_flag, metainfo=None):
    if alert_flag:
        if metainfo:
            response += "\n" + str(metainfo)
        return response + "\n\n🔔 Activated"
    return response


def decision_to_bool(decision: str) -> bool:
    return "yes" in decision.lower()


def run(
    *,
    object_id=os.environ.get("FILE_OR_DIRECTORY_ID", ""),
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
    service_user_credentials_file=os.environ.get(
        "GOOGLE_CREDS", "examples/pipelines/drive_alert/secrets.json"
    ),
    **kwargs,
):
    # Part I: Build index
    embedder = OpenAIEmbeddingModel(api_key=api_key)

    # We start building the computational graph. Each pathway variable represents a
    # dynamically changing table.

    # The files table contains contents of documents in Google Drive.
    # Pathway automatically tracks changes to files and propagates these changes through
    # following computations.
    # Other Pathway connectors can be used as well - notably:
    # - pw.io.fs.read to load and track changes to the local drive and
    # - pw.io.s3.read to use an S3-compatible storage
    files = pw.io.gdrive.read(
        object_id=object_id,
        service_user_credentials_file=service_user_credentials_file,
        refresh_interval=30,  # interval between fetch operations in seconds, lower this for more responsiveness
    )
    documents = files.select(texts=extract_texts(pw.this.data))
    documents = documents.select(
        chunks=chunk_texts(pw.this.texts, min_tokens=40, max_tokens=120)
    )
    documents = documents.flatten(pw.this.chunks).rename_columns(doc=pw.this.chunks)

    enriched_documents = documents + documents.select(
        data=embedder.apply(text=pw.this.doc, locator=embedder_locator)
    )

    # The index is updated each time a file changes.
    index = KNNIndex(
        enriched_documents.data, enriched_documents, n_dimensions=embedding_dimension
    )

    # Part II: receive queries, detect intent and prepare cleaned query

    # The rest_connector returns a table of all queries under processing
    query, response_writer = pw.io.http.rest_connector(
        host=host,
        port=port,
        schema=QueryInputSchema,
        autocommit_duration_ms=50,
        delete_completed_queries=False,
    )

    model = OpenAIChatGPTModel(api_key=api_key)

    # Pre-process the queries:
    # - detect alerting intent
    # - then embed the query for nearest neighbor retrieval
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

    # The context is a dynamic table: Pathway updates it each time:
    # - a new query arrives
    # - a source document is changed significantly enough to change the set of
    #   nearest neighbors
    query_context = query + index.get_nearest_items(query.data, k=3).select(
        documents_list=pw.this.doc
    ).with_universe_of(query)

    # then we answer the queries using retrieved documents
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

    # and send the answers back to the asking users
    response_writer(output)

    # Part IV: send alerts about responses which changed significantly.

    # However, for the queries with alerts the processing continues
    # whenever the set of documents retrieved for a query changes,
    # the table of responses is updated.
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

    # Each update is compared with the previous one for deduplication
    deduplicated_responses = pw.stateful.deduplicate(
        responses,
        col=responses.response,
        acceptor=acceptor,
        instance=responses.query_id,
    )

    # Significant alerts are sent to the user
    alerts = deduplicated_responses.select(
        message=construct_notification_message(pw.this.query, pw.this.response)
    )
    send_slack_alerts(alerts.message, slack_alert_channel_id, slack_alert_token)

    # Finally, we execute the computation graph
    pw.run(monitoring_level=pw.MonitoringLevel.NONE)


if __name__ == "__main__":
    run()
