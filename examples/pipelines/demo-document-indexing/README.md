# Realtime Document Indexing with Pathway

This is a basic service for a real-time document indexing pipeline powered by [Pathway](https://github.com/pathwaycom/pathway).

The capabilities of the pipeline include:
    
- Real-time document indexing from Microsoft 365 SharePoint, Google Drive, or a local directory;
- Similarity search by user query;
- Filtering by the metadata according to the condition given in [JMESPath format](https://jmespath.org/);
- Basic stats on the indexer's health.

## Summary of the Pipeline

This example spawns a lightweight webserver that accepts queries on three possible endpoints:
- `/v1/retrieve` to perform similarity search;
- `/v1/statistics` to get the basic stats about the indexer's health;
- `/v1/inputs` to retrieve the metadata of all files currently processed by the indexer.

Please refer to the Open API doc on Hosted Pipelines [website](https://pathway.com/solutions/ai-pipelines) for the format of the requests to the endpoints.

## How It Works

This pipeline uses several Pathway connectors to read the data from the local drive, Google Drive, and Microsoft SharePoint sources. It allows you to poll the changes with low latency and to do the modifications tracking. So, if something changes in the tracked files, the corresponding change is reflected in the internal collections. The contents are read into a single Pathway Table as binary objects. 

After that, those binary objects are parsed with [unstructured](https://unstructured.io/) library and split into chunks. With the usage of OpenAI API, the pipeline embeds the obtained chunks.

Finally, the embeddings are indexed with the capabilities of Pathway's machine-learning library. The user can then query the created index with simple HTTP requests to the endpoints mentioned above.

## Pipeline Organization

This folder contains several objects:
- `main.py`, the pipeline code using Pathway and written in Python;
- `sources_configuration.yaml`, the file containing configuration stubs for the data sources. It needs to be customized if you want to use the Google Drive data source or to change the filesystem directories that will be indexed;
- `requirements.txt`, the textfile denoting the pip dependencies for running this pipeline. It can be passed to `pip install -r ...` to install everything that is needed to launch the pipeline locally;
- `Dockerfile`, the Docker configuration for running the pipeline in the container;
- `docker-compose.yml`, the docker-compose configuration for running the pipeline along with the chat UI;
- `.env`, a short environment variables configuration file where the OpenAI key must be stored;
- `files-for-indexing/`, a folder with exemplary files that can be used for the test runs.

## OpenAPI Key Configuration

This example relies on the usage of OpenAI API, which is crucial to perform the embedding part.

**You need to have a working OpenAI key stored in the environment variable OPENAI_API_KEY**.

Please configure your key in a `.env` file by providing it as follows: `OPENAI_API_KEY=sk-*******`. You can refer to the stub file `.env` in this repository, where you will need to paste your key instead of `sk-*******`.

## Sources configuration

You can configure data sources used for indexing by editing the configuration file. Here we provide the template config `sources_configuration.yaml` for these purposes. It contains stubs for the three possible input types - please refer to the examples.

Each section of the config requires the specification of a data source type along with its parameters, such as the filesystem path, credentials, etc. The available kinds are `local`, `gdrive`, and `sharepoint`. The sections below describe the essential parameters that need to be specified for each of those sources.

### Local Data Source

The local data source is configured by setting the `kind` parameter to `local`.

The section `config` must contain the string parameter `path` denoting the path to a folder with files to be indexed.

For the full list of the available configuration options, please refer to the filesystem connector [documentation](https://pathway.com/developers/api-docs/pathway-io/gdrive#pathway.io.fs.read).

### Google Drive Data Source

The Google Drive data source is enabled by setting the `kind` parameter to `gdrive`.

The section `config` must contain two main parameters:
- `object_id`, containing the ID of the folder that needs to be indexed. It can be found from the URL in the web interface, where it's the last part of the address. For example, the publicly available demo folder in Google Drive has the URL `https://drive.google.com/drive/folders/1cULDv2OaViJBmOfG5WB0oWcgayNrGtVs`. Consequently, the last part of this address is `1cULDv2OaViJBmOfG5WB0oWcgayNrGtVs`, hence this is the `object_id` you would need to specify.
- `service_user_credentials_file`, containing the path to the credentials files for the Google [service account](https://cloud.google.com/iam/docs/service-account-overview). To get more details on setting up the service account and getting credentials, you can also refer to [this tutorial](https://pathway.com/developers/user-guide/connectors/gdrive-connector/#setting-up-google-drive).

Besides, to speed up the indexing process you may want to specify the `refresh_interval` parameter, denoted by an integer number of seconds. It corresponds to the frequency between two sequential folder scans. If unset, it defaults to 30 seconds.

For the full list of the available parameters, please refer to the Google Drive connector [documentation](https://pathway.com/developers/api-docs/pathway-io/gdrive#pathway.io.gdrive.read).

#### Using Provided Demo Folder

We provide a publicly available folder in Google Drive for demo purposes; you can access it [here](https://drive.google.com/drive/folders/1cULDv2OaViJBmOfG5WB0oWcgayNrGtVs).

A default configuration for the Google Drive source in `sources_configuration.yaml` is available and connects to the folder: uncomment the corresponding part and replace `SERVICE_CREDENTIALS` with the path to the credentials file.

Once connected, you can upload files to the folder, which will be indexed by Pathway.
Note that this folder is publicly available, and you cannot remove anything: **please be careful not to upload files containing any sensitive information**.

#### Using a Custom Folder

If you want to test the indexing pipeline with the data you wouldn't like to share with others, it's possible: with your service account, you won't have to share the folders you've created in your private Google Drive.

Therefore, all you would need to do is the following:
- Create a service account and download the credentials that will be used;
- For running the demo, create your folder in Google Drive and don't share it.

### SharePoint Data Source

This data source is the part of commercial Pathway offering. You can try it online in one of the following demos:
- The real-time document indexing pipeline with similarity search, available on the [Hosted Pipelines](https://pathway.com/solutions/ai-pipelines) webpage;
- The chatbot answering questions about the uploaded files, available on [Streamlit](https://chat-realtime-sharepoint-gdrive.demo.pathway.com/).

## Running the Example

### Locally

This example can be run locally by executing `python main.py` in this directory. It has several command-line arguments:
- `--host` denoting the host, where the server will run. The default setting is `0.0.0.0`;
- `--port` denoting the port, where the server will accept requests. The default setting is `8000`;
- `--sources-config` pointing to a data source configuration file, `sources_configuration.yaml` by default. You can customize it to change the folders indexed by the vector store. The free version supports `local` and `gdrive` hosted files, while the commercial one also supports `sharepoint` hosted folders. By default, the `local` option indexes files from the `files-for-indexing/` folder that is prefilled with exemplary documents.

Please note that the local run requires the dependencies to be installed. It can be done with a simple pip command:

```bash
pip install -r requirements.txt
```

### With Docker

First, create or fill the `.env` file in this folder (`/demo-document-indexing`) with your OpenAI key `OPENAI_API_KEY=sk-*******`.

To run jointly the vector indexing pipeline and a simple UI please execute:

```bash
docker compose up --build
```

Then, the UI will run at http://127.0.0.1:8501 by default. You can access it by following this URL in your web browser.

The `docker-compose.yml` file declares a [volume bind mount](https://docs.docker.com/reference/cli/docker/container/run/#volume) that makes changes to files under `files-for-indexing/` made on your host computer visible inside the docker container. If the index does not react to file changes, please check that the bind mount works 
by running `docker compose exec pathway_vector_indexer ls -l /app/files-for-indexing/` and verifying that all files are visible.

Alternatively, you can launch just the indexing pipeline as a single Docker container:

```bash
docker build -t vector_indexer .
docker run -v `pwd`/files-for-indexing:/app/files-for-indexing vector_indexer
```

The volume overlay is important - without it, docker will not see changes to files under the `files-for-indexing` folder.

## Querying the Example

Since the pipeline spawns an HTTP server and interacts with the user using the REST protocol, you can test it locally by sending requests with `curl`. To get the target address for the request, you can refer to the routes in the first section: `v1/retrieve`, `v1/statistics`, and `v1/inputs` and the Open API docs available at the Hosted Pipelines webpage.

Let's assume that the server runs with the default settings and therefore uses port 8000. That being said, you can query the similarity search endpoint with the following command:

```bash
curl -X 'GET' \
  'http://localhost:8000/v1/retrieve?query=Pathway%20data%20processing%20framework&k=2' \
  -H 'accept: */*'
```

Above, there are two CGI parameters to be customized: the `query`, which should contain the [urlencoded](https://en.wikipedia.org/wiki/Percent-encoding) search terms, and an integer `k` denoting the number of documents you want to retrieve.

Apart from the querying part, there is a health-check endpoint that shows the number of documents currently indexed and the most recent indexing time. It can be accessed, in a similar way, with the following command:

```bash
curl -X 'GET' \
  'http://localhost:8000/v1/statistics' \
  -H 'accept: */*'
```

Finally, there is a way to see the metadata of all documents that are currently indexed. To do that, you need to query the `v1/inputs` endpoint. The request command then looks as follows:

```bash
curl -X 'GET' \
  'http://localhost:8000/v1/inputs' \
  -H 'accept: */*'
```

Please make sure that you've changed the port in the requests if you did that when launching the main script.

## Adding Files to Index

To test index updates, simply add more files to the `files-for-indexing` folder if the local data source is used. 
If you are using Google Drive, simply upload your files in the folder configured in the `sources_configuration.yaml` file.

Then you can use the similarity search and stats endpoints, provided below.
