<p align="center">
    <a href="https://github.com/pathwaycom/llm-app-pathway/blob/main/LICENSE">
        <img src="https://img.shields.io/github/license/pathwaycom/llm-app-pathway?style=plastic" alt="Contributors"/></a>
    <a href="https://github.com/pathwaycom/llm-app-pathway/graphs/contributors">
        <img src="https://img.shields.io/github/contributors/pathwaycom/llm-app-pathway?style=plastic" alt="Contributors"/></a>
    <a href="https://github.com/pathwaycom/llm-app-pathway/actions/workflows/install_package.yml">
        <img src="https://img.shields.io/github/actions/workflow/status/pathwaycom/llm-app-pathway/install_package.yml?style=plastic" alt="Build" /></a> 
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

Pathway's **LLM App** is a chatbot application which provides real-time responses to user queries, based on the freshest knowledge available in a document store. It does not require a separate vector database, and helps to avoid fragmented LLM stacks (such as ~Pinecone/Weaviate + Langchain + Redis + FastAPI +...~). Document data lives in the place where it was stored already, and on top of this, LLM App provides a light but integrated data processing layer, which is highly performant and can be easily customized and extended. It is particulary recommended for privacy-preserving LLM applications.

## Project Overview

LLM App reads a corpus of documents stored in S3 or locally, preprocesses them, and builds a vector index by calling a routine from the Pathway package. It then listens to user queries coming as HTTP REST requests. Each query uses the index to retrieve relevant documentation snippets and uses the OpenAI API/ Hugging Face to provide a response in natural language. The bot is reactive to changes in the corpus of documents: once new snippets are provided, it reindexes them and starts to use the new knowledge to answer subsequent queries.

### Watch a Demo Here
(Available soon)


### Key Features
- **HTTP REST queries:** The system is capable of responding in real-time to HTTP REST queries.
- **Real-time document indexing pipeline:** This pipeline reads data directly from S3-compatible storage, without the need to query a vector document database.
- **User session and beta testing handling:** The query building process can be extended to handle user sessions and beta testing for new models.
- **Code reusability for offline evaluation:** The same code can be used for static evaluation of the system.

## Getting Started

### Installation

Clone the repository. Create a new environment and install the required packages:

```bash
python -m venv pw-env && source pw-env/bin/activate
cd llm-app-pathway/
pip install --upgrade --extra-index-url https://packages.pathway.com/966431ef6ba -r requirements.txt
```
### Usage

- Create an .env file in `llm_app/` directory and add the following environment variables:
```bash
PATHWAY_REST_CONNECTOR_HOST=127.0.0.1
PATHWAY_REST_CONNECTOR_PORT=8080
OPENAI_API_TOKEN=<Your Token>
PATHWAY_CACHE_DIR=/tmp/cache
```

- Run the script using the command: 
```bash 
cd llm_app/
python main.py --mode contextful
```
You can also run the app without the need for external APIs by using `local` mode.

- Send REST queries (in a separate terminal window):
```bash
curl --data '{"user": "user", "query": "How to connect to Kafka in Pathway?"}' http://localhost:8080/ | jq

curl --data '{"user": "user", "query": "How to use LLMs in Pathway?"}' http://localhost:8080/ | jq
```

- Test reactivity by adding a new file:
```bash
cp ./data/documents_extra.jsonl ./data/pathway-docs/
curl --data '{"user": "user", "query": "How to use LLMs in Pathway?"}' http://localhost:8080/ | jq
```

### Data Privacy and Use in Organizations

LLM App can be configured to run with local Machine Learning models, without making API calls outside of the User's Organization.

It can also be extended to handle live data sources (news feeds, API's, data streams in Kafka), to include user permissions, a data security layer, and an LLMops monitoring layer.

See: [Features for Organizations](FEATURES-for-organizations.md).

## Further Reading
Read more about the implementation details and how to extend this application in our [blog series](https://pathway.com/blog/?tag=tutorial).

## Supported and maintained by:

<div align="center">
  <a href="https://github.com/pathwaycom/"><img src="https://pathway.com/logo-light.svg" /></a>
</div>
