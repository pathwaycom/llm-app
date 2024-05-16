# Contextful Pipeline

This example implements a pipeline that answers questions based on documents in a given folder. To get the answer it sends increasingly more documents to the LLM chat until it can find an answer. You can read more about the reasoning behind this approach [here](https://pathway.com/developers/showcases/adaptive-rag).

Each query text is first turned into a vector using OpenAI embedding service,
then relevant documentation pages are found using a Nearest Neighbor index computed
for documents in the corpus. A prompt is built from the relevant documentations pages
and sent to the OpenAI chat service for processing.

To optimize use of tokens per query, this pipeline asks a question with a small number
of documents embedded in the prompt. If OpenAI chat fails to answer based on these documents,
the number of documents is increased by `factor` given as an argument, and continues to
do so until either question is answered or a limit of iterations is reached.

## How to run the project

### Setup environment:
Set your env variables in the .env file placed in this directory or in the root of the repo.

```bash
OPENAI_API_KEY=sk-...
PATHWAY_DATA_DIR= # If unset, defaults to ../../data/pathway-docs/
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
