# Realtime Document Indexing with Pathway

This is a basic service for a real-time document indexing pipeline powered by [Pathway](https://github.com/pathwaycom/pathway).

## Running the Example 🚀

This example spawns a lightweight webserver that accepts queries on three possible endpoints:
- `/v1/retrieve` to perform similarity search;
- `/v1/statistics` to get the basic stats about the indexer's health;
- `/v1/inputs` to retrieve the metadata of all files currently processed by the indexer.

Please refer to the Open API doc on Hosted Pipelines [website](https://cloud.pathway.com/) for the format of the requests to the endpoints.

This example can be run by executing `python main.py` in this directory. It has several command-line arguments:
- `--host` denoting the host, where the server will run. The default setting is `0.0.0.0`;
- `--port` denoting the port, where the server will accept requests. The default setting is `8000`;
- `--sources-config` points to a datasource configuration file, `sources_configuration.yaml` by default. You can customize it to change the fodlers indexed by the vector store. The free version supports `local` and `gdrive` hosted files, while the commercial one also supports `sharepoint` hosted folders. By default, the `local` option indexes files from the `files-for-indexing/` folder that is prefilled with exemplary documents.

## Running with docker
First create an `.env` file in this folder (`/demo-document-indexing`) with your OpenAI key `OPENAI_API_KEY=sk-`. 

To run jointly the vector indexing pipeline and a simple UI please execute:

```bash
cd examples/pipelines/demo-document-indexing
echo "Then UI will launch at http://127.0.0.1:8501 by default"
docker compose up --build
```

The `docker-compose.yml` file declares a [volume bind mount](https://docs.docker.com/reference/cli/docker/container/run/#volume) that makes changes to files under `files-for-indexing/` made on your host computer visible inside the docker container. If the index does not react to file changes, please check that the bind mount works 
by running `docker compose exec pathway_vector_indexer ls -l /app/files-for-indexing/` and verifying that all files are visible.

Alternatively, you can launch just the indexing pipeline as a single Docker container:

```bash
cd examples/pipelines/demo-document-indexing

docker build -t vector_indexer .
docker run -v `pwd`/files-for-indexing:/app/files-for-indexing vector_indexer
```

The volume overlay is important - without it docker will not see changes to file under the `files-for-indexing` folder.

## Adding Files to Index 💾
    
To test index updates, simply add more files to the `files-for-indexing/` folder if the local data source is used. 

Then you can use the similarity search and stats endpoints, provided below.

## Capabilities 🛠️
    
The capabilities of the service include:
    
- Real-time document indexing from Microsoft 365 SharePoint, Google Drive, or a local directory;
- Similarity search by user query;
- Filtering by the metadata according to the condition given in [JMESPath format](https://jmespath.org/);
- Basic stats on the indexer's health.
    
Supported document formats include plaintext, pdf, docx, and HTML. For the complete list, please refer to the supported formats of the [unstructured](https://github.com/Unstructured-IO/unstructured) library.

In addition, this pipeline is capable of data removals: you can delete files and in a few seconds, a similarity search will undo the changes done to the index by their addition.
