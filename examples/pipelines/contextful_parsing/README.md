# Contextful Parsing Pipeline

This example implements a RAG pipeline, similarly to [contextful pipeline](). It uses, however, [Unstructured](https://unstructured.io/) library for parsing documents, e.g. PDFs, which are then split into smaller chunks. 

## How to run the project

### Setup environment:
Set your env variables in the .env file placed in this directory or in the root of the repo.

```bash
OPENAI_API_KEY=sk-...
PATHWAY_DATA_DIR= # If unset, defaults to ./data/
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

If all dependencies are managed manually rather than using poetry, you can also use:

```bash
python app.py
```

To query the pipeline, you can call the REST API:

```bash
curl --data '{
  "user": "user",
  "query": "When does the magic cola campaign start? Alert me if the start date changes."
}' http://localhost:8080/ | jq
```

or use the Streamlit UI. Run:
```bash
streamlit run ui/server.py --server.port 8501 --server.address 0.0.0.0
```
and then you can access the UI at `0.0.0.0:8501`.
