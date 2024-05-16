# Local Pipeline

This pipeline is similar to the [contextful pipeline](),  but relies on local computations, rather than querying external API. To do that it uses [HuggingFace](https://huggingface.co/) for the chat model and [Sentence Transformers](https://www.sbert.net/) for the embedding model.

## How to run the project

### Setup environment:
Set your env variables in the .env file placed in this directory or in the root of the repo.

```bash
PATHWAY_DATA_DIR= # If unset, defaults to ../../data/pathway-docs-small/
PATHWAY_PERSISTENT_STORAGE= # Set this variable if you want to use caching
```

### Run the project

Make sure you have installed poetry dependencies with `--extras local`. 

```bash
poetry install --with examples --extras local
```

Run:

```bash
poetry run python app.py
```

If all dependencies are managed manually rather than using poetry, you can also use:

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
