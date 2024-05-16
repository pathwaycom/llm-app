# Alert Pipeline

This example implements a pipeline that answers questions based on documents in a given folder. Additionally, in your prompts you can ask to be notified of any changes - in such case an alert will be sent to a Slack channel.

Upon starting, a REST API endpoint is opened by the app to serve queries about files inside
the input folder `data_dir`.

We can create notifications by sending a query to API and stating we want to be notified of the changes.
One example would be `Tell me and alert about the start date of the campaign for Magic Cola`

What happens next?

Each query text is first turned into a vector using OpenAI embedding service,
then relevant documentation pages are found using a Nearest Neighbor index computed
for documents in the corpus. A prompt is built from the relevant documentations pages
and sent to the OpenAI GPT3.5 chat service for processing and answering.

Once you run, Pathway looks for any changes in data sources and efficiently detects changes
to the relevant documents. When a change is detected, the LLM is asked to answer the query
again, and if the new answer is sufficiently different, an alert is created.

## How to run the project

### Setup Slack notifications:

For this demo, Slack notifications are optional and notifications will be printed if no Slack API keys are provided. See: [Slack Apps](https://api.slack.com/apps) and [Getting a token](https://api.slack.com/tutorials/tracks/getting-a-token).
Your Slack application will need at least `chat:write.public` scope enabled.

### Setup environment:
Set your env variables in the .env file placed in this directory or in the root of the repo.

```bash
OPENAI_API_KEY=sk-...
SLACK_ALERT_CHANNEL_ID=  # If unset, alerts will be printed to the terminal
SLACK_ALERT_TOKEN=
PATHWAY_DATA_DIR= # If unset, defaults to ../../data/magic-cola/live/
PATHWAY_PERSISTENT_STORAGE= # Set this variable if you want to use caching
```

### Run the project

Make sure you have installed poetry dependencies with `--extras unstructured`. 

```bash
poetry install --with examples --extras unstructured
```

Run:

```bash
poetry run python app.py
```

If all dependencies are managed manually rather than using poetry, you can run:

```bash
python app.py
```

To create alerts, you can call the REST API:

```bash
curl --data '{
  "user": "user",
  "query": "When does the magic cola campaign start? Alert me if the start date changes."
}' http://localhost:8080/ | jq
```
