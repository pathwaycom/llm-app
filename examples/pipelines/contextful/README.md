<p align="left">
  <a href="https://pathway.com/developers/user-guide/deployment/gcp-deploy" style="display: inline-flex; align-items: center;">
    <img src="https://www.gstatic.com/pantheon/images/welcome/supercloud.svg" alt="GCP Logo" height="1.2em"> <span style="margin-left: 5px;">Deploy with GCP</span>
  </a> | 
  <a href="https://pathway.com/developers/user-guide/deployment/render-deploy" style="display: inline-flex; align-items: center;">
    <img src="../../../assets/render.png" alt="Render Logo" height="1.2em"> <span style="margin-left: 5px;">Deploy with Render</span>
  </a>
</p>

# RAG pipeline with up-to-date knowledge: get answers based on documents in local folder

This example implements a simple pipeline that answers questions based on documents in a given folder.

Each query text is first turned into a vector using OpenAI embedding service,
then relevant documentation pages are found using a Nearest Neighbor index computed
for documents in the corpus. A prompt is built from the relevant documentation pages
and sent to the OpenAI chat service for processing.

## How to run the project

### Setup environment:
Set your env variables in the .env file placed in this directory.

```bash
OPENAI_API_KEY=sk-...
PATHWAY_DATA_DIR= # If unset, defaults to ./data/. If running with Docker, when you change this variable you may need to change the volume mount.
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

To query the pipeline, you can call the REST API:

```bash
curl --data '{
  "user": "user",
  "query": "How to connect to Kafka in Pathway?"
}' http://localhost:8080/ | jq
```

or access the Streamlit UI at `0.0.0.0:8501`.
