<div align="center">

[![Pathway banner](https://d14l3brkh44201.cloudfront.net/pathway-llm.png)](https://pathway.com/)

# LLM App

[![LICENSE](https://img.shields.io/github/license/pathwaycom/llm-app?style=plastic)](https://github.com/pathwaycom/llm-app/blob/main/LICENSE)
[![Contributors](https://img.shields.io/github/contributors/pathwaycom/llm-app?style=plastic)](https://github.com/pathwaycom/llm-app/graphs/contributors)

<!--- [![Contributors](https://img.shields.io/github/actions/workflow/status/pathwaycom/llm-app/install_package.yml?style=plastic)](https://github.com/pathwaycom/llm-app/actions/workflows/install_package.yml) --->
![Linux](https://img.shields.io/badge/OS-Linux-green)
![macOS](https://img.shields.io/badge/OS-macOS-green)
[![chat on Discord](https://img.shields.io/discord/1042405378304004156?logo=discord)](https://discord.gg/pathway)
[![follow on Twitter](https://img.shields.io/twitter/follow/pathway_com?style=social&logo=twitter)](https://twitter.com/intent/follow?screen_name=pathway_com)
</div>

Pathway's **LLM (Large Language Model) App** is a Python library that helps you create and launch AI-powered applications based on the most up-to-date knowledge available in your data sources. You can use it to answer natural language queries asked by your users, or to run data transformation pipelines with LLM's.

**Quick links** - 👀[Why LLM App?](#why-llm-app) 💡[Use cases](#use-cases) 📚 [How it works](#how-it-works) 🌟 [Key Features](#key-features) 🏁 [Get Started](#get-started) 🎬 [Showcases](#showcases) 🛠️ [Troubleshooting](#troubleshooting)
👥 [Contributing](#troubleshooting)

## Why LLM App?

1. **Simplicity** - Simplifies your AI pipeline by consolidating capabilities into one platform. No need to integrate and maintain separate modules for your Gen AI app: ~Vector Databases (e.g. Pinecone/Weaviate/Qdrant) + LangChain + Cache (e.g. Redis) + API Framework (e.g. Fast API)~.
2. **Real-time data syncing** - Syncs both structured and unstructured data from diverse sources, enabling real-time Retrieval Augmented Generation (RAG).
3. **Easy alert setup** - Configure alerts for key business events with simple configurations.
4. **Scalability** - Handles heavy data loads and usage without degradation in performance. Metrics help track usage and scalability.
5. **Monitoring** - Provide visibility into model behavior via monitoring, tracing errors, anomaly detection, and replay for debugging. Helps with response quality.
6. **Security** - Designed for the enterprise with capabilities like Personally Identifiable Information (PII) detection, content moderation, permissions, and version control. Run this in your private cloud with local LLMs.

## Use cases

LLM App examples can be used as templates for developing multiple applications running on top of Pathway. Here are examples of possible uses:

* **Build your own Discord AI chatbot** that answers questions (this is what you see covered in the video!). Or any similar AI chatbot.
* **Ask privacy-preserving queries** to an LLM using a private knowledge base that is frequently updated.
* **Extend Kafka-based streaming architectures with LLMs**.
* **Process LLM queries in bulk** with prompts created automatically out of input data streams.
* **Obtain structured data on the fly** out of streams of documents.
* **Validate incoming documents** against existing documents with an LLM.
* **Monitor live information streams** with an LLM: news and social media, spotting fake news, travel disruptions...

## How it works

The default [`contextful`](examples/pipelines/contextful/app.py) pipeline launches an application which connects to a source folder with documents, stored in [AWS S3](https://aws.amazon.com/s3/) or locally on your computer. The app is always in sync with updates to your documents, building in real-time a "vector index" using the Pathway package. It waits for user queries that come as HTTP REST requests, then uses the index to find relevant documents and responds using [OpenAI API](https://openai.com/blog/openai-api) or [Hugging Face](https://huggingface.co/) in natural language. This way, it provides answers that are always best on the freshest and most accurate **real-time data**.

The app can also be combined with streams of fresh data, such as news feeds or status reports, either through REST or a technology like Kafka. It can also be combined with extra static data sources and user-specific contexts, for example, to eliminate **the ambiguity problems** of natural language with clearer prompts and better contexts.

Read more about the implementation details and how to extend this application in [our blog article](https://pathway.com/developers/showcases/llm-app-pathway/).

### Watch it in action

[![Build your LLM App without a vector database (in 30 lines of code)](https://d14l3brkh44201.cloudfront.net/video-th.png)](https://www.youtube.com/watch?v=kcrJSk00duw)

▶️ [Building an LLM Application without a vector database](https://www.youtube.com/watch?v=kcrJSk00duw) - by [Jan Chorowski](https://scholar.google.com/citations?user=Yc94070AAAAJ)


## Features

### Key Features

* **HTTP REST queries** - The system is capable of responding in real-time to HTTP REST queries.
* **Real-time document indexing pipeline** - This pipeline reads data directly from S3-compatible storage, without the need to query an extra vector document database.
* **Code reusability for offline evaluation** - The same code can be used for static evaluation of the system.
* **Model testing** - Present and past queries can be run against fresh models to evaluate their quality.

### Advanced Features

* **Local Machine Learning models** - LLM App can be configured to run with local Machine Learning models, without making API calls outside of the User's Organization.

* **Live data sources** - The library can be used to handle live data sources (news feeds, APIs, data streams in Kafka), as well as to include user permissions, a data security layer, and an LLMops monitoring layer.

* **User session handling** - The library's query-building process can be used to handle user sessions.

* To learn more about advanced features see: [Features for Organizations](FEATURES-for-organizations.md).

### Coming Soon

* Splitting the application into indexing and request-serving processes easily.
* Expanding context doc selection with a graph walk / support for a HNSW variant.
* Model drift and monitoring setup.
* A guide to model A/B testing.


## Get Started

### Prerequisites

1. Make sure that [Python](https://www.python.org/downloads/) 3.10 or above installed on your machine.
2. Download and Install [Pip](https://pip.pypa.io/en/stable/installation/) to manage project packages.
3. [Optional if you use OpenAI models]. Create an [OpenAI](https://openai.com/) account and generate a new API Key: To access the OpenAI API, you will need to create an API Key. You can do this by logging into the [OpenAI website](https://openai.com/product) and navigating to the API Key management page.
4. [Important if you use Windows OS]. Example only supports Unix-like systems (such as Linux, macOS, BSD). If you are a Windows user, we highly recommend leveraging [Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/install) or Dockerize the app to run as a container.
5. [Optional if you use Docker to run samples]. Download and install [docker](https://www.docker.com/).

To get started explore one of the examples:

| Example                                                    | Description                                                                                                                                                                                                                                                                                                                             |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`contextless`](examples/pipelines/contextless/app.py)     | This simple example calls OpenAI ChatGPT API but does not use an index when processing queries. It relies solely on the given user query. We recommend it to start your Pathway LLM journey.                                                                                                                                            |
| [`contextful`](examples/pipelines/contextful/app.py)       | This default example of the app will index the jsonlines documents located in the `data/pathway-docs` directory. These indexed documents are then taken into account when processing queries. The pathway pipeline being run in this mode is located at [`examples/pipelines/contextful/app.py`](examples/pipelines/contextful/app.py). |
| [`contextful_s3`](examples/pipelines/contextful_s3/app.py) | This example operates similarly to the contextful mode. The main difference is that the documents are stored and indexed from an S3 bucket, allowing the handling of a larger volume of documents. This can be more suitable for production environments.                                                                               |
| [`unstructured`](examples/pipelines/unstructured/app.py)   | Process unstructured documents such as PDF, HTML, DOCX, PPTX and more. Visit [unstructured-io](https://unstructured-io.github.io/unstructured/) for the full list of supported formats.                                                                                                                                                 |
| [`local`](examples/pipelines/local/app.py)                 | This example runs the application using Huggingface Transformers, which eliminates the need for the data to leave the machine. It provides a convenient way to use state-of-the-art NLP models locally.                                                                                                                                 |
| [`unstructuredtosql`](examples/pipelines/unstructured_to_sql_on_the_fly/app.py) | This example extracts the data from unstructured files and store it into a postgres table. It also transforms the user query into a SQL query which is executed on the postgres table.                                                                                                                                 |

Follow these easy steps to install and get started with your favorite examples. You can also take a look at the [application showcases](#showcases).

### Step 1: Clone the repository

This is done with the `git clone` command followed by the URL of the repository:

```bash
git clone https://github.com/pathwaycom/llm-app.git
```

Next, navigate to the repository:

```bash
cd llm-app
```

### Step 2: Set environment variables

Create an .env file in the root directory and add the following environment variables, adjusting their values according to your specific requirements and setup.

| Environment Variable        | Description                                                                                                                                                                                                                                              |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| APP_VARIANT                 | Determines which pipeline to run in your application. Available modes are [`contextful`, `s3`, `contextless`, `local`, `unstructuredtosql`]. By default, the mode is set to `contextful`.                                                                                       |
| PATHWAY_REST_CONNECTOR_HOST | Specifies the host IP for the REST connector in Pathway. For the dockerized version, set itto `0.0.0.0` Natively, you can use `127.0.01`                                                                                                                 |
| PATHWAY_REST_CONNECTOR_PORT | Specifies the port number on which the REST connector service of the Pathway should listen.Here, it is set to8080.                                                                                                                                       |
| OPENAI_API_TOKEN            | The API token for accessing OpenAI services. If you are not running the local version, pleaseremember to replace it with your personal API token, which you can generate from your account on [openai.com](https:/platform.openai.com/account/api-keys). |
| PATHWAY_CACHE_DIR           | Specifies the directory where cache is stored. You could use /tmpcache.                                                                                                                                                                                  |

For example:

```bash
APP_VARIANT=contextful
PATHWAY_REST_CONNECTOR_HOST=0.0.0.0
PATHWAY_REST_CONNECTOR_PORT=8080
OPENAI_API_TOKEN=<Your Token>
PATHWAY_CACHE_DIR=/tmp/cache
```

### Step 3: Build and run the app

You can install and run the LLM App in two different ways.

#### Using Docker

Docker is a tool designed to make it easier to create, deploy, and run applications by using containers. Here is how to use Docker to build and run the LLM App:

```bash
docker compose run --build --rm -p 8080:8080 llm-app-examples
```

If you have set a different port in `PATHWAY_REST_CONNECTOR_PORT`, replace the second `8080` with this port in the command above.

When the process is complete, the App will be up and running inside a Docker container and accessible at `0.0.0.0:8080`. From there, you can proceed to the "Usage" section of the documentation for information on how to interact with the application.

#### Native Approach

* **Install poetry:**

    ```bash
    pip install poetry
    ```

* **Install llm_app and dependencies:**

    ```bash
    poetry install --with examples --extras local
    ```

    You can omit `--extras local` part if you're not going to run local example.

* **Run the examples:** You can start the example with the command:

    ```bash
    poetry run ./run_examples.py contextful
    ```

### Step 4: Start to use it

1. **Send REST queries** (in a separate terminal window): These are examples of how to interact with the application once it's running. `curl` is a command-line tool used to send data using various network protocols. Here, it's being used to send HTTP requests to the application.

    ```bash
    curl --data '{"user": "user", "query": "How to connect to Kafka in Pathway?"}' http://localhost:8080/

    curl --data '{"user": "user", "query": "How to use LLMs in Pathway?"}' http://localhost:8080/
    ```

    If you are on windows CMD, then the query would rather look like this

    ```cmd
    curl --data "{\"user\": \"user\", \"query\": \"How to use LLMs in Pathway?\"}" http://localhost:8080/
    ```

2. **Test reactivity by adding a new file:** This shows how to test the application's ability to react to changes in data by adding a new file and sending a query.

    ```bash
    cp ./data/documents_extra.jsonl ./data/pathway-docs/
    ```

    Or if using docker compose:

    ```bash
    docker compose exec llm-app-examples mv /app/examples/data/documents_extra.jsonl /app/examples/data/pathway-docs/
    ```

    Let's query again:

    ```bash
    curl --data '{"user": "user", "query": "How to use LLMs in Pathway?"}' http://localhost:8080/
    ```

### Step 5: Launch the User Interface:
Go to the `examples/ui/` directory (or `examples/pipelines/unstructured/ui` if you are running the unstructured version.) and execute `streamlit run server.py`. Then, access the URL displayed in the terminal to engage with the LLM App using a chat interface.

### Bonus: Build your own Pathway-powered LLM App

Simply add `llm-app` to your project's dependencies and copy one of the examples to get started!

## Showcases

* [Python sales](https://github.com/Boburmirzo/chatgpt-api-python-sales) - Find real-time sales with AI-powered Python API using ChatGPT and LLM (Large Language Model) App.

* [Dropbox Data Observability](https://github.com/pathway-labs/dropbox-ai-chat) - See how to get started with chatting with your Dropbox and having data observability. 


## Troubleshooting

Please check out our [Q&A](https://github.com/pathwaycom/llm-app/discussions/categories/q-a) to get solutions for common installation problems and other issues.

### Raise an issue

To provide feedback or report a bug, please [raise an issue on our issue tracker](https://github.com/pathwaycom/llm-app/issues).

## Contributing

Anyone who wishes to contribute to this project, whether documentation, features, bug fixes, code cleanup, testing, or code reviews, is very much encouraged to do so.

To join, just raise your hand on the [Pathway Discord server](https://discord.com/invite/pathway) (#get-help) or the GitHub [discussion](https://github.com/pathwaycom/llm-app/discussions) board.

If you are unfamiliar with how to contribute to GitHub projects, here is a [Get Started Guide](https://docs.github.com/en/get-started/quickstart/contributing-to-projects). A full set of contribution guidelines, along with templates, are in progress.

## Supported and maintained by

<div align="center">
  <a href="https://github.com/pathwaycom/"><img src="https://pathway.com/logo-light.svg" /></a>
</div>

<p align="center">
  Pathway is a free ultra-performant data processing framework
to power your real-time data products and pipelines. To learn more, checkout <a href="https://pathway.com/">Pathway's website</a>.
</p>
