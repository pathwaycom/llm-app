<p align="left">
  <a href="https://pathway.com/developers/user-guide/deployment/gcp-deploy" style="display: inline-flex; align-items: center;">
    <img src="https://www.gstatic.com/pantheon/images/welcome/supercloud.svg" alt="GCP Logo" height="1.2em"> <span style="margin-left: 5px;">Deploy with GCP</span>
  </a> | 
  <a href="https://pathway.com/developers/user-guide/deployment/render-deploy" style="display: inline-flex; align-items: center;">
    <img src="../../../assets/render.png" alt="Render Logo" height="1.2em"> <span style="margin-left: 5px;">Deploy with Render</span>
  </a>
</p>

# Real-time alerting based on local documents: End-to-end template

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
Set your env variables in the .env file placed in this directory.

```bash
OPENAI_API_KEY=sk-...
SLACK_ALERT_CHANNEL_ID=
SLACK_ALERT_TOKEN=
PATHWAY_DATA_DIR= # If unset, defaults to ./data/live/. If running with Docker, when you change this variable you may need to change the volume mount.
PATHWAY_PERSISTENT_STORAGE= # Set this variable if you want to use caching
```

### Run with Docker

To run jointly the Alert pipeline and a simple UI execute:

```bash
docker compose up --build
```

Then, the UI will run at http://0.0.0.0:8501 by default. You can access it by following this URL in your web browser.

The `docker-compose.yml` file declares a [volume bind mount](https://docs.docker.com/reference/cli/docker/container/run/#volume) that makes changes to files under `data/` made on your host computer visible inside the docker container. The files in `data/live` are indexed by the pipeline - you can paste new files there and they will impact the computations.

### Run manually

Alternatively, you can run each service separately.

Make sure you have installed poetry dependencies. 
```bash
poetry install --with examples
```

Then run:
```bash
poetry run python app.py
```

If all dependencies are managed manually rather than using poetry, you can alternatively use:
```bash
python app.py
```

To run the Streamlit UI, run:
```bash
streamlit run ui/server.py --server.port 8501 --server.address 0.0.0.0
```

### Querying the pipeline

To create alerts, you can call the REST API:

```bash
curl --data '{
  "user": "user",
  "query": "When does the magic cola campaign start? Alert me if the start date changes."
}' http://localhost:8080/ | jq
```

or access the Streamlit UI at `0.0.0.0:8501`.
