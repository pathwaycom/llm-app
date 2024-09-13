<p align="left">
  <a href="https://pathway.com/developers/user-guide/deployment/gcp-deploy" style="display: inline-flex; align-items: center;">
    <img src="https://www.gstatic.com/pantheon/images/welcome/supercloud.svg" alt="GCP Logo" height="1.2em"> <span style="margin-left: 5px;">Deploy with GCP</span>
  </a> | 
  <a href="https://pathway.com/developers/user-guide/deployment/render-deploy" style="display: inline-flex; align-items: center;">
    <img src="../../../assets/render.png" alt="Render Logo" height="1.2em"> <span style="margin-left: 5px;">Deploy with Render</span>
  </a>
</p>

# Pathway RAG app with always up-to-date knowledge

This demo shows how to create a RAG application using [Pathway](https://github.com/pathwaycom/pathway) that provides always up-to-date knowledge to your LLM without the need for a separate ETL. 

You can have a preview of the demo [here](https://pathway.com/solutions/ai-pipelines).

You will see a running example of how to get started with the Pathway vector store that eliminates the need for ETL pipelines which are needed in the regular VectorDBs. 
This significantly reduces the developer's workload.

This demo allows you to:

- Create a vector store with real-time document indexing from Google Drive, Microsoft 365 SharePoint, or a local directory;
- Connect an OpenAI LLM model of choice to your knowledge base;
- Get quality, accurate, and precise responses to your questions;
- Ask questions about folders, files or all your documents easily, with the help of filtering options;
- Use LLMs over API to summarize texts;
- Get an executive outlook for a question on different files to easily access available knowledge in your documents;


Note: This app relies on [Pathway Vector store](https://pathway.com/developers/api-docs/pathway-xpacks-llm/vectorstore) to learn more, you can check out [this blog post](https://pathway.com/developers/user-guide/llm-xpack/vectorstore_pipeline/).

# Table of content
- [Summary of available endpoints](#Summary-of-available-endpoints)
- [How it works](#How-it-works)
- [Configuring the app](#Configuration)
- [How to run the project](#How-to-run-the-project)
- [Using the app](#Query-the-documents)


## Summary of available endpoints

This example spawns a lightweight webserver that accepts queries on six possible endpoints, divided into two categories: document indexing and RAG with LLM.

### Document Indexing capabilities
- `/v1/retrieve` to perform similarity search;
- `/v1/statistics` to get the basic stats about the indexer's health;
- `/v1/pw_list_documents` to retrieve the metadata of all files currently processed by the indexer.

### LLM and RAG capabilities
- `/v1/pw_ai_answer` to ask questions about your documents, or directly talk with your LLM;
- `/v1/pw_ai_summary` to summarize a list of texts;

See the [using the app section](###Using-the-app) to learn how to use the provided endpoints.

## How it works

This pipeline uses several Pathway connectors to read the data from the local drive, Google Drive, and Microsoft SharePoint sources. It allows you to poll the changes with low latency and to do the modifications tracking. So, if something changes in the tracked files, the corresponding change is reflected in the internal collections. The contents are read into a single Pathway Table as binary objects. 

After that, those binary objects are parsed with [unstructured](https://unstructured.io/) library and split into chunks. With the usage of OpenAI API, the pipeline embeds the obtained chunks.

Finally, the embeddings are indexed with the capabilities of Pathway's machine-learning library. The user can then query the created index with simple HTTP requests to the endpoints mentioned above.

## Pipeline Organization

This folder contains several objects:
- `app.py`, the application code using Pathway and written in Python;
- `config.yaml`, the file containing configuration stubs for the data sources, the OpenAI LLM model, and the web server. It needs to be customized if you want to change the LLM model, use the Google Drive data source or change the filesystem directories that will be indexed;
- `requirements.txt`, the dependencies for the pipeline. It can be passed to `pip install -r ...` to install everything that is needed to launch the pipeline locally;
- `Dockerfile`, the Docker configuration for running the pipeline in the container;
- `.env`, a short environment variables configuration file where the OpenAI key must be stored;
- `data/`, a folder with exemplary files that can be used for the test runs.

## Pathway tooling
- Prompts and helpers

Pathway allows you to define custom prompts in addition to the ones provided in [`pathway.xpacks.llm`](https://pathway.com/developers/user-guide/llm-xpack/overview).

You can also use user-defined functions using the [`@pw.udf`](https://pathway.com/developers/api-docs/pathway/#pathway.udf) decorator to define custom functions that will run on streaming data.

- RAG

Pathway provides all the tools to create a RAG application and query it: a [Pathway vector store](https://pathway.com/developers/api-docs/pathway-xpacks-llm/splitters) and a web server (defined with the [REST connector](https://pathway.com/developers/api-docs/pathway-io/http#pathway.io.http.rest_connector)).
They are defined in our demo in the main class `PathwayRAG` along with the different functions and schemas used by the RAG.

For the sake of the demo, we kept the app simple, consisting of the main components you would find in a regular RAG application. It can be further enhanced with query writing methods, re-ranking layer and custom splitting steps.

Don't hesitate to take a look at our [documentation](https://pathway.com/developers/user-guide/introduction/welcome) to learn how Pathway works.


## OpenAI API Key Configuration

This example relies on the usage of OpenAI API, which is crucial to perform the embedding part.

**You need to have a working OpenAI key stored in the environment variable OPENAI_API_KEY**.

Please configure your key in a `.env` file by providing it as follows: `OPENAI_API_KEY=sk-*******`. You can refer to the stub file `.env` in this repository, where you will need to paste your key instead of `sk-*******`.

You can also set the key in the `app.py` while initializing the embedder and chat instances as follows;

```python
chat = llms.OpenAIChat(api_key='sk-...', ...)

embedder = embedders.OpenAIEmbedder(api_key='sk-...', ...)
```

If you want to use another model, you should put the associated key here.

## Configuration

By modifying the `conf.yaml` file, you can configure the following options:
- the Open AI LLM model
- the webserver
- the cache options
- the data sources

### Model

You can choose any of the GPT-3.5 Turbo, GPT-4, or GPT-4 Turbo models proposed by Open AI.
You can find the whole list on their [models page](https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo).

You simply need to change the model to the one you want to use:
```yaml
llm_config:
  model: "gpt-4-0613"
```

The default model is `gpt-3.5-turbo`

Note that if you want to use different models, such as the ones provided by HuggingFace, you will need to change the `run` function in `app.py`. You can use [Pathway LLM xpack](https://pathway.com/developers/user-guide/llm-xpack/overview) to access the model of your choice. Don't forget to update your key.

### Webserver

You can configure the host and the port of the webserver.
Here is the default configuration:
```yaml
host_config:
  host: "0.0.0.0"
  port: 8000
```

### Cache

You can configure whether you want to enable cache, to avoid repeated API accesses, and where the cache is stored.
Default values:
```yaml
cache_options:
  with_cache: True
  cache_folder: "./Cache"
```

### Data sources

You can configure the data sources in the `config.source` part of the `conf.yaml`.
You can add as many data sources as you want, but the demo supports only three kinds: `local`, `gdrive`, and `sharepoint`. You can have several sources of the same kind, for instance, several local sources from different folders.
The sections below describe the essential parameters that need to be specified for each of those sources.

By default, the app uses a local data source to read documents from the `data` folder.

You can use other kind of data sources using the different [connectors](https://pathway.com/developers/user-guide/connecting-to-data/connectors) provided by Pathway.
To do so, you need to add them in `data_sources` in `app.py`


#### Local Data Source

The local data source is configured by setting the `kind` parameter to `local`.

The section `config` must contain the string parameter `path` denoting the path to a folder with files to be indexed.

#### Google Drive Data Source

The Google Drive data source is enabled by setting the `kind` parameter to `gdrive`.

The section `config` must contain two main parameters:
- `object_id`, containing the ID of the folder that needs to be indexed. It can be found from the URL in the web interface, where it's the last part of the address. For example, the publicly available demo folder in Google Drive has the URL `https://drive.google.com/drive/folders/1cULDv2OaViJBmOfG5WB0oWcgayNrGtVs`. Consequently, the last part of this address is `1cULDv2OaViJBmOfG5WB0oWcgayNrGtVs`, hence this is the `object_id` you would need to specify.
- `service_user_credentials_file`, containing the path to the credentials files for the Google [service account](https://cloud.google.com/iam/docs/service-account-overview). To get more details on setting up the service account and getting credentials, you can also refer to [this tutorial](https://pathway.com/developers/user-guide/connectors/gdrive-connector/#setting-up-google-drive).

Besides, to speed up the indexing process you may want to specify the `refresh_interval` parameter, denoted by an integer number of seconds. It corresponds to the frequency between two sequential folder scans. If unset, it defaults to 30 seconds.

For the full list of the available parameters, please refer to the Google Drive connector [documentation](https://pathway.com/developers/api-docs/pathway-io/gdrive#pathway.io.gdrive.read).

#### Using the Provided Demo Folder

We provide a publicly available folder in Google Drive for demo purposes; you can access it [here](https://drive.google.com/drive/folders/1cULDv2OaViJBmOfG5WB0oWcgayNrGtVs).

A default configuration for the Google Drive source in `config.yaml` is available and connects to the folder: uncomment the corresponding part and replace `SERVICE_CREDENTIALS` with the path to the credentials file.

Once connected, you can upload files to the folder, which will be indexed by Pathway.
Note that this folder is publicly available, and you cannot remove anything: **please be careful not to upload files containing any sensitive information**.

#### Using a Custom Folder

If you want to test the indexing pipeline with the data you wouldn't like to share with others, it's possible: with your service account, you won't have to share the folders you've created in your private Google Drive.

Therefore, all you would need to do is the following:
- Create a service account and download the credentials that will be used;
- For running the demo, create your folder in Google Drive and don't share it.

#### SharePoint Data Source

This data source is the part of commercial Pathway offering. You can try it online in one of the following demos:
- The real-time document indexing pipeline with similarity search, available on the [Hosted Pipelines](https://pathway.com/solutions/ai-pipelines) webpage;
- The chatbot answering questions about the uploaded files, available on [Streamlit](https://chat-realtime-sharepoint-gdrive.demo.pathway.com/).

## How to run the project

### Locally
If you are on Windows, please refer to [running with docker](#With-Docker) section below.

To run locally, change your directory in the terminal to this folder. Then, run the app with `python`.

```bash
cd examples/pipelines/demo-question-answering

python app.py
```

Please note that the local run requires the dependencies to be installed. It can be done with a simple pip command:
`pip install -r requirements.txt`

### With Docker

In order to let the pipeline get updated with each change in local files, you need to mount the folder onto the docker. The following commands show how to do that.

You can omit the ```-v `pwd`/data:/app/data``` part if you are not using local files as a source. 
```bash
# Make sure you are in the right directory.
cd examples/pipelines/demo-question-answering

# Build the image in this folder
docker build -t qa .

# Run the image, mount the `data` folder into image and expose the port `8000`
docker run -v `pwd`/data:/app/data -p 8000:8000 qa
```

### Query the documents
You will see the logs for parsing & embedding documents in the Docker image logs. 
Give it a few minutes to finish up on embeddings, you will see `0 entries (x minibatch(es)) have been...` message.
If there are no more updates, this means the app is ready for use!

To test it, let's query the stats:
```bash
curl -X 'POST'   'http://localhost:8000/v1/statistics'   -H 'accept: */*'   -H 'Content-Type: application/json'
```

For more information on available endpoints by default, see [API docs](https://pathway.com/solutions/ai-pipelines).

We provide some example `curl` queries to start with.

The general structure is sending a request to `http://{HOST}:{PORT}/{ENDPOINT}`.

Where HOST is the `host` variable you specify in your app configuration. PORT is the `port` number you are running your app on, and ENDPOINT is the specific extension for endpoints. They are specified in the application code, and they are listed with the versioning as `/v1/...`.

Note that, if you are using the Pathway hosted version, you should send requests to `https://...` rather than `http://...` and emit the `:{PORT}` part of the URL.

You need to add two headers, `-H 'accept: */*'   -H 'Content-Type: application/json'`.

Finally, for endpoints that expect data in the query, you can pass it with `-d '{key: value}'` format.

#### Listing inputs
Get the list of available inputs and associated metadata.

```bash
curl -X 'POST'   'http://localhost:8000/v1/pw_list_documents'   -H 'accept: */*'   -H 'Content-Type: application/json'
```

#### Searching in your documents

Search API gives you the ability to search in available inputs and get up-to-date knowledge.
`query` is the search query you want to execute.

`k` (optional) is an integer, the number of documents to be retrieved. Documents in this case means small chunks that are stored in your vector store.

`metadata_filter` (optional) String to filter results with Jmespath query.

`filepath_globpattern` (optional) String to filter results with globbing pattern. For example `"*"` would result in no filter, `"*.docx"` would result in only `docx` files being retrieved.


```bash
curl -X 'POST' \
  'http://0.0.0.0:8000/v1/retrieve' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "What is the start date of the contract?",
  "k": 2
}'
```

#### Asking questions to LLM (With and without RAG)

- Note: The local version of this app does not require `openai_api_key` parameter in the payload of the query. Embedder and LLM will use the API key in the `.env` file. However, Pathway hosted public demo available on the website [website](https://pathway.com/solutions/ai-pipelines/) requires a valid `openai_api_key` to execute the query.

- Note: All of the RAG endpoints use the `model` provided in the config by default, however, you can specify another model with the `model` parameter in the payload to use a different one for generating the response.

For question answering without any context, simply omit `filters` key in the payload and send the following request.

```bash
curl -X 'POST' \
  'http://0.0.0.0:8000/v1/pw_ai_answer' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -d '{
  "prompt": "What is the start date of the contract?"
}'
```

Question answering with the knowledge from files that have the word `Ide` in their paths.
```bash
curl -X 'POST' \
  'http://0.0.0.0:8000/v1/pw_ai_answer' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -d '{
  "prompt": "What is the start date of the contract?",
  "filters": "contains(path, `Ide`)"
}'
```

- Note: You can limit the knowledge to a folder or, to only Word documents by using ```"contains(path, `docx`)"```
- Note: You could also use a few filters separated with `||` (`or` clause) or with `&&` (`and` clause).

You can further modify behavior in the payload by defining keys and values in `-d '{key: value}'`.

If you wish to use another model, specify in the payload as `"model": "gpt-4"`.

For more detailed responses add `"response_type": "long"` to payload.

#### Summarization
To summarize a list of texts, use the following `curl` command.

```bash
curl -X 'POST' \
  'http://0.0.0.0:8000/v1/pw_ai_summary' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -d '{
  "text_list": [
    "I love apples.",
    "I love oranges."
  ]
}'
```

Specifying the GPT model with `"model": "gpt-4"` is also possible.

This endpoint also supports setting different models in the query by default.

To execute similar curl queries as above, you can visit [ai-pipelines page](https://pathway.com/solutions/ai-pipelines/) and try out the queries from the Swagger UI.


#### Adding Files to Index

First, you can try adding your files and seeing changes in the index. To test index updates, simply add more files to the `data` folder.

If you are using Google Drive or other sources, simply upload your files there.
