<p align="left">
  <a href="https://pathway.com/developers/user-guide/deployment/gcp-deploy" style="display: inline-flex; align-items: center;">
    <img src="https://www.gstatic.com/pantheon/images/welcome/supercloud.svg" alt="GCP Logo" height="1.2em"> <span style="margin-left: 5px;">Deploy with GCP</span>
  </a> | 
  <a href="https://pathway.com/developers/user-guide/deployment/render-deploy" style="display: inline-flex; align-items: center;">
    <img src="../../../assets/render.png" alt="Render Logo" height="1.2em"> <span style="margin-left: 5px;">Deploy with Render</span>
  </a>
</p>

# Local Pipeline

This pipeline is similar to the [contextful pipeline](),  but relies on local computations, rather than querying external API. To do that it uses [HuggingFace](https://huggingface.co/) for the chat model and [Sentence Transformers](https://www.sbert.net/) for the embedding model.

## How to run the project

### Setup environment:
Set your env variables in the .env file placed in this directory or in the root of the repo.

```bash
PATHWAY_DATA_DIR= # If unset, defaults to ./data/
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

or use the Streamlit UI. Run:
```bash
streamlit run ui/server.py --server.port 8501 --server.address 0.0.0.0
```
and then you can access the UI at `0.0.0.0:8501`.
