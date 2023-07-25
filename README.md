<p align="center">
    <a href="https://github.com/pathwaycom/llm-app/blob/main/LICENSE">
        <img src="https://img.shields.io/github/license/pathwaycom/llm-app?style=plastic" alt="Contributors"/></a>
    <a href="https://github.com/pathwaycom/llm-app/graphs/contributors">
        <img src="https://img.shields.io/github/contributors/pathwaycom/llm-app?style=plastic" alt="Contributors"/></a>
    <!--<a href="https://github.com/pathwaycom/llm-app/actions/workflows/install_package.yml">
        <img src="https://img.shields.io/github/actions/workflow/status/pathwaycom/llm-app/install_package.yml?style=plastic" alt="Build" /></a> -->
        <img src="https://img.shields.io/badge/OS-Linux-green" alt="Linux"/>
        <img src="https://img.shields.io/badge/OS-macOS-green" alt="macOS"/>
      <br>
    <a href="https://discord.gg/pathway">
        <img src="https://img.shields.io/discord/1042405378304004156?logo=discord"
            alt="chat on Discord"></a>
    <a href="https://twitter.com/intent/follow?screen_name=pathway_com">
        <img src="https://img.shields.io/twitter/follow/pathway_com?style=social&logo=twitter"
            alt="follow on Twitter"></a>
</p>

# LLM App

Pathway's **LLM App** is a chatbot application which provides real-time responses to user queries, based on the freshest knowledge available in a document store. It does not require a separate vector database, and helps to avoid fragmented LLM stacks (such as ~Pinecone/Weaviate + Langchain + Redis + FastAPI +...~). Document data lives in the place where it was stored already, and on top of this, LLM App provides a light but integrated data processing layer, which is highly performant and can be easily customized and extended. It is particularly recommended for privacy-preserving LLM applications.

## Project Overview

LLM App reads a corpus of documents stored in S3 or locally, preprocesses them, and builds a vector index by calling a routine from the Pathway package. It then listens to user queries coming as HTTP REST requests. Each query uses the index to retrieve relevant documentation snippets and uses the OpenAI API/ Hugging Face to provide a response in natural language. The bot is reactive to changes in the corpus of documents: once new snippets are provided, it reindexes them and starts to use the new knowledge to answer subsequent queries.

### Watch a Demo
[![Build your LLM App without a vector database (in 30 lines of code)](https://img.youtube.com/vi/kcrJSk00duw/0.jpg)](https://www.youtube.com/watch?v=kcrJSk00duw)

▶️ [Building an LLM Application without a vector database](https://www.youtube.com/watch?v=kcrJSk00duw) - by [Jan Chorowski](https://scholar.google.com/citations?user=Yc94070AAAAJ)


### Key Features
- **HTTP REST queries:** The system is capable of responding in real-time to HTTP REST queries.
- **Real-time document indexing pipeline:** This pipeline reads data directly from S3-compatible storage, without the need to query a vector document database.
- **User session and beta testing handling:** The query building process can be extended to handle user sessions and beta testing for new models.
- **Code reusability for offline evaluation:** The same code can be used for static evaluation of the system.

### Coming Soon:
- Splitting the application into indexing and request-serving processes easily.
- Controlling which model is used.
- Expanding context doc selection with a graph walk.
- Model drift and monitoring setup.
- Model A/B testing support.


## Getting Started

This section provides a general introduction on how to start using the app. You can run it in different settings:

| Pipeline Mode   | Description                                                                                                                                                                                                                                                                        |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `contextful`    | In this mode, the app will index the documents located in the `data/pathway-docs` directory. These indexed documents are then taken into account when processing queries. The pathway pipeline being run in this mode is located at `llm_app/pathway_pipelines/contextful/app.py`. |
| `contextful_s3` | This mode operates similarly to the contextful mode. The main difference is that the documents are stored and indexed from an S3 bucket, allowing the handling of a larger volume of documents. This can be more suitable for production environments.                             |
| `contextless`   | This pipeline calls OpenAI ChatGPT API but does not use an index when processing queries. It relies solely on the given user query.                                                                                                                                                |
| `local`         | This mode runs the application using Huggingface Transformers, which eliminates the need for the data to leave the machine. It provides a convenient way to use state-of-the-art NLP models locally.                                                                               |

### Installation


- **Clone the repository:** This is done with the `git clone` command followed by the URL of the repository:
    ```bash
    git clone https://github.com/pathwaycom/llm-app.git
    ```
    Next, navigate to the repository:
    ```bash
    cd llm-app
    ```


- **Environment Variables:** Create an .env file in `llm_app/` directory and add the following environment variables, adjusting their values according to your specific requirements and setup.

    | Environment Variable        | Description                                                                                                                                                                                                                                                |
    | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
    | PIPELINE_MODE               | Determines which pipeline to run in your application. Available modes are [`contextful`, `contextful_s3`, `contextless`, `local`]. By default, the mode is set to `contextful`.                                                                            |
    | PATHWAY_REST_CONNECTOR_HOST | Specifies the host IP for the REST connector in Pathway. For the dockerized version, set it to `0.0.0.0` Natively, you can use `127.0.0.1`                                                                                                                 |
    | PATHWAY_REST_CONNECTOR_PORT | Specifies the port number on which the REST connector service of the Pathway should listen. Here, it is set to 8080.                                                                                                                                       |
    | OPENAI_API_TOKEN            | The API token for accessing OpenAI services. If you are not running the local version, please remember to replace it with your personal API token, which you can generate from your account on [openai.com](https://platform.openai.com/account/api-keys). |
    | PATHWAY_CACHE_DIR           | Specifies the directory where cache is stored. You could use /tmp/cache.                                                                                                                                                                                   |
    

    ```bash
    PIPELINE_MODE=contextful
    PATHWAY_REST_CONNECTOR_HOST=0.0.0.0
    PATHWAY_REST_CONNECTOR_PORT=8080
    OPENAI_API_TOKEN=<Your Token>
    PATHWAY_CACHE_DIR=/tmp/cache
    ```

#### Using Docker:

Docker is a tool designed to make it easier to create, deploy, and run applications by using containers. Here is how to use Docker to build and run the LLM App:

  - **Build and Run with Docker** The first step is to build the Docker image for the LLM App. You do this with the docker build command.
    Build the image:
    ```bash
    docker compose build
    ```
    After your image is built, you can run it as a container. You use the docker compose run command to do this
    ```bash
    docker compose run -p 8080:8080 llm-app
    ```
    If you have set a different port in `PATHWAY_REST_CONNECTOR_PORT`, replace the second `8080` with this port in the command above.
    
    When the process is complete, the App will be up and running inside a Docker container and accessible at `0.0.0.0:8080`. From there, you can proceed to the "Usage" section of the documentation for information on how to interact with the application.

#### Native Approach:

**Important:** The instructions in this section are intended for users operating Unix-like systems (such as Linux, macOS, BSD). If you are a Windows user, we highly recommend leveraging Windows Subsystem for Linux (WSL) or Docker, as outlined in the previous sections, to ensure optimal compatibility and performance.

- **Virtual Python Environment:** Create a new environment and install the required packages to isolate the dependencies of this project from your system's Python:

    ```bash
    # Creates an env called pw-env and activates this environment.
    python -m venv pw-env && source pw-env/bin/activate

    pip install --upgrade -r requirements.txt
    ```

- **Run the App:** You can start the application with the command:
    ```bash 
    cd llm_app/
    python main.py
    ```

### Usage

1. **Send REST queries** (in a separate terminal window): These are examples of how to interact with the application once it's running. `curl` is a command-line tool used to send data using various network protocols. Here, it's being used to send HTTP requests to the application.
    ```bash
    curl --data '{"user": "user", "query": "How to connect to Kafka in Pathway?"}' http://localhost:8080/ | jq

    curl --data '{"user": "user", "query": "How to use LLMs in Pathway?"}' http://localhost:8080/ | jq
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
    docker compose exec llm-app mv /app/data/documents_extra.jsonl /app/data/pathway-docs/
    ```
    Let's query again:
    ```
    curl --data '{"user": "user", "query": "How to use LLMs in Pathway?"}' http://localhost:8080/ | jq
    ```

### Data Privacy and Use in Organizations

LLM App can be configured to run with local Machine Learning models, without making API calls outside of the User's Organization.

It can also be extended to handle live data sources (news feeds, API's, data streams in Kafka), to include user permissions, a data security layer, and an LLMops monitoring layer.

See: [Features for Organizations](FEATURES-for-organizations.md).

## How is it done?

Read more about the implementation details and how to extend this application in [our blog article](https://pathway.com/developers/showcases/llm-app-pathway/).

## Supported and maintained by:

<div align="center">
  <a href="https://github.com/pathwaycom/"><img src="https://pathway.com/logo-light.svg" /></a>
</div>
