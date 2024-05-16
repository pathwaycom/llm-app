# Contextless Pipeline

This example implements a pipeline that answers a single question, without any context.

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
