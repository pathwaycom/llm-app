# Contextful S3 Pipeline

This example implements a simple pipeline that answers questions based on documents stored in S3.

Each query text is first turned into a vector using OpenAI embedding service,
then relevant documentation pages are found using a Nearest Neighbor index computed
for documents in the corpus. A prompt is built from the relevant documentations pages
and sent to the OpenAI chat service for processing.

## How to run the project

### Setup environment:
Set your env variables in the .env file placed in this directory or in the root of the repo.

```bash
OPENAI_API_KEY=sk-...
PATHWAY_PERSISTENT_STORAGE= # Set this variable if you want to use caching
```

### Run the project

```bash
poetry install --with examples
```

Run:

```bash
poetry run python app.py
```

If all dependencies are managed manually rather than using poetry, you can run either:

```bash
python app.py
```

To query the pipeline, you can call the REST API:

```bash
curl --data '{
  "user": "user",
  "query": "How to connect to Kafka in Pathway?"
}' http://localhost:8080/ | jq
```

or use the Streamlit UI. Run:
```bash
streamlit run ui/server.py --server.port 8501 --server.address 0.0.0.0
```
and then you can access the UI at `0.0.0.0:8501`.
