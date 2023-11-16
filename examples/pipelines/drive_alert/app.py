"""
Microservice for a context-aware alerting ChatGPT assistant.

This demo is very similar to `alert` example, only difference is the data source (Google Drive)
For the demo, alerts are sent to the Slack (you need `slack_alert_channel_id` and `slack_alert_token`), you can
either put these env variables in .env file under llm-app directory,
or create env variables in terminal (ie. export in bash)
If you don't have Slack, you can leave them empty and app will print the notifications instead.

The program then starts a REST API endpoint serving queries about input folder `data_dir`.

We can create notifications by asking from Streamlit or sending query to API stating we want to be modified.
One example would be `Tell me and alert about start date of campaign for Magic Cola`

How It Works?
We sync a local folder with Google Drive, whenever there is a change, Pathway captures it.
Native support for Drive to Pathway can be also added with Python connectors.

Each query text is first turned into a vector using OpenAI embedding service,
then relevant documentation pages are found using a Nearest Neighbor index computed
for documents in the corpus. A prompt is build from the relevant documentations pages
and sent to the OpenAI GPT3.5 chat service for processing and answering.

Once you run, Pathway looks for any changes in data sources, if any change is done, pipeline is triggered.
If new answer is different than the previous one, a notification is created.

Setting up before use:
Download rclone:
https://rclone.org/downloads/


Follow config steps here:
https://rclone.org/drive/#configuration

During config, it will ask `Use web browser to automatically authenticate rclone with remote?`
If you are working on your own computer, press enter or say `Y` and you will be prompted to authorize.
You can skip following if you accessed browser and authorized the app.

If you are on a virtual machine with no browser access, see below.
        You need this only if you are working on virtual machine!!!

        Open a terminal where you can execute Python or an empty notebook,
        install dependencies
        ```
        pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
        ```

        Run the following code, it will prompt an URL, go there and give permission
        ```
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        creds = None
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'creds.txt', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        ```
        You need this only if you are working on virtual machine!!!

You are ready to go!

If you need client and and secret, follow the guide here:
https://rclone.org/drive/#making-your-own-client-id

Usage:
First, set you env variables in .env file placed in root of repo
`OPENAI_API_KEY=sk-...
PATHWAY_REST_CONNECTOR_HOST=127.0.0.1
PATHWAY_REST_CONNECTOR_PORT=8181
SLACK_ALERT_CHANNEL_ID=
SLACK_ALERT_TOKEN=
REMOTE_NAME=<<your config name from rclone>>
REMOTE_FOLDER=magic-cola #  folder name under your google drive
TRACKED_FILE=staging/campaign.docx  # file that is under the folder you want to track
LOCAL_FOLDER=./examples/data/magic-cola/local-drive/`  # synced drive in local

In the root of this repository run:
`poetry run examples/pipelines/drive_alert/drive_script.py`
keep this open.

In another terminal,
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

from examples.example_utils import find_last_modified_file, get_file_info
from llm_app import chunk_texts, deduplicate, extract_texts, send_slack_alerts
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
    return str(hash(query + user))  # + str(time.time())


@pw.udf
def construct_notification_message(query: str, response: str, metainfo=None) -> str:
    return f'New response for question "{query}":\n{response}\nFrom: {str(metainfo)}'


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
        "PATHWAY_DATA_DIR", "./examples/data/magic-cola/local-drive/staging/"
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

    files = pw.io.fs.read(
        data_dir,
        mode="streaming_with_deletions",  # streaming, streaming_with_deletions
        format="binary",
        autocommit_duration_ms=50,
        object_pattern="*.docx",
    )
    documents = files.select(texts=extract_texts(pw.this.data))
    documents = documents.select(
        chunks=chunk_texts(pw.this.texts, min_tokens=40, max_tokens=120)
    )
    documents = documents.flatten(pw.this.chunks).rename_columns(doc=pw.this.chunks)

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
        delete_completed_queries=False,
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

        if "mention" in new or "cannot" in new or "inferred" in new:
            return False

        if "mention" in old or "cannot" in old or "inferred" in old:
            return True

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

    pw.run(monitoring_level=pw.MonitoringLevel.NONE)


if __name__ == "__main__":
    run()
