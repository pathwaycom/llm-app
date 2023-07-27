<p align="center">
    <a href="https://github.com/pathwaycom/llm-app/blob/main/LICENSE">
        <img src="https://img.shields.io/github/license/pathwaycom/llm-app?style=plastic" alt="Contributors"/></a>
    <a href="https://github.com/pathwaycom/llm-app/graphs/contributors">
        <img src="https://img.shields.io/github/contributors/pathwaycom/llm-app?style=plastic" alt="Contributors"/></a>
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

# LLM App: Mircroservices Architecture

The LLM application is a multi-service software that consists of three main components: the Controller, the LLM, and the Embedder. These services communicate with each other through REST Connector to provide the functionality of the overall application.

The application has been dockerized and can be easily deployed using Docker Compose.

## Get Started:

### Services:
- **Controller:** The main entry point for the application. It runs the index and coordinates with the other services. It exposes port 8080 for external communication.
- **LLM:** This service performs the core functionality related to the LLM module of the application.
- **Embedder:** This service is responsible for the embedding operations within the application.

### Requirements
- Docker
- Docker Compose

### Setup
1. Clone the repository to your local machine.
2. Navigate to the directory containing the Docker Compose file: `llm_app/pathway_pipelines/multi_service`.
3. Create a `.env` file in the same directory as the Docker Compose file. This file should contain all the necessary environment variables required by the services.
    Example:
    ```bash
    MODEL_LOCATOR=llama-2-7b.ggmlv3.q2_K.bin
    EMBEDDER_LOCATOR=sentence-transformers/all-MiniLM-L6-v2
    PATHWAY_REST_CONNECTOR_HOST=0.0.0.0
    PATHWAY_REST_CONNECTOR_PORT=8080
    MODEL_REST_CONNECTOR_HOST=0.0.0.0
    MODEL_REST_CONNECTOR_PORT=8888
    EMBEDDER_REST_CONNECTOR_HOST=0.0.0.0
    EMBEDDER_REST_CONNECTOR_PORT=8880
    PATHWAY_CACHE_DIR=/tmp/cache
    ```
    The LLM used is a [python api](https://github.com/abetlen/llama-cpp-python) for [Llama cpp](https://github.com/ggerganov/llama.cpp) model which is to be downloaded prior to running the app.
    For instance, to use Llama-2-7B with q2_K quantization method, download it from HuggingFace using:
    ```bash 
    wget https://huggingface.co/localmodels/Llama-2-7B-ggml/resolve/main/llama-2-7b.ggmlv3.q2_K.bin
    ```

4. Running the application
    Run the following command in the same directory as your Docker Compose file to build and start the services:

    ```bash
    docker-compose up --build
    ```
    To stop the services, press CTRL+C in the terminal where you ran the command, or run the following command:

    ```bash
    docker-compose down
    ```

### Debugging
All services are started with stdin_open and tty enabled, which means you can attach to the running containers for interactive debugging. Use the following command to attach to a running container:

```bash
docker attach <container_id>
```
Replace <container_id> with the ID of the container you wish to debug. You can find this ID using the docker ps command.


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