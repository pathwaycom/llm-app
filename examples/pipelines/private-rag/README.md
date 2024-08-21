<p align="left">
  <a href="https://pathway.com/developers/user-guide/deployment/gcp-deploy" style="display: inline-flex; align-items: center;">
    <img src="https://www.gstatic.com/pantheon/images/welcome/supercloud.svg" alt="GCP Logo" height="1.2em"> <span style="margin-left: 5px;">Deploy with GCP</span>
  </a> | 
  <a href="https://pathway.com/developers/user-guide/deployment/render-deploy" style="display: inline-flex; align-items: center;">
    <img src="../../../assets/render.png" alt="Render Logo" height="1.2em"> <span style="margin-left: 5px;">Deploy with Render</span>
  </a>
</p>

# Fully private RAG with Pathway

## **Overview**

Retrieval-Augmented Generation (RAG) is a powerful method for answering questions using a private knowledge database. Ensuring data security is essential, especially for sensitive information like trade secrets, confidential IP, GDPR-protected data, and internal documents. This showcase demonstrates setting up a private RAG pipeline with adaptive retrieval using Pathway, Mistral, and Ollama. The provided code deploys this adaptive RAG technique with Pathway, ensuring no API access or data leaves the local machine.

The app utilizes modules under `pathway.xpacks.llm`. The `BaseRAGQuestionAnswerer` class is the foundation for building RAG applications with the Pathway vector store and xpack components, enabling a quick start with RAG applications.

This example uses `AdaptiveRAGQuestionAnswerer`, an extension of `BaseRAGQuestionAnswerer` with adaptive retrieval. For more on building and deploying RAG applications with Pathway, including containerization, refer to the demo on question answering.

The application responds to requests at the `/v1/pw_ai_answer` endpoint. The `pw_ai_query` function takes the `pw_ai_queries` table as input, containing prompts and other arguments from the post request. This table's data is used to call the adaptive retrieval logic.

The `AdaptiveRAGQuestionAnswerer` implementation under `pathway.xpacks.llm.question_answering` builds a RAG app with the Pathway vector store and components. It supports two question answering strategies, short (concise) and long (detailed) responses, set during the post request. It allows LLM agnosticity, giving the freedom to choose between proprietary or open-source LLMs. It adapts the number of chunks used as a context, starting with `n_starting_documents` chunks and increasing until an answer is found.

To learn more about building & deploying RAG applications with Pathway, including containerization, refer to [demo question answering](../demo-question-answering/README.md).


## Table of contents

This includes the technical details to the steps to create a REST Endpoint to run the application via Docker and modify it for your use-cases.

- [Overview](#Overview)
- [Architecture](#Architecture)
- [Deploying and using a local LLM](#Deploying-and-using-a-local-LLM)
- [Running the app](#Running-the-app)
- [Querying the app/pipeline](#Querying-the-app/pipeline)
- [Modifying the code](#Modifying-the-code)
- [Conclusion](#Conclusion)


## Architecture

![Architecture](https://i.imgur.com/9TJEoUd.png)

The architecture consists of two connected technology bricks, which will run as services on your machine:
- Pathway brings support for real-time data synchronization pipelines out of the box, and the possibility of secure private document handling with enterprise connectors for synchronizing Sharepoint and Google Drive incrementally. The Pathway service you'll run performs live document indexing pipeline, and will use Pathway’s built-in vector store.
- The language model you use will be a Mistral 7B, which you will locally deploy as an Ollama service. This model was chosen for its performance and compact size.


## Deploying and using a local LLM


### Embedding Model Selection

You will use `pathway.xpacks.llm.embedders` module to load open-source embedding models from the HuggingFace model library. For this showcase, pick the `avsolatorio/GIST-small-Embedding-v0` model which has a dimension of 384 as it is compact and performed well in our tests. 

```python 
embedding_model = "avsolatorio/GIST-small-Embedding-v0"

embedder = embedders.SentenceTransformerEmbedder(
    embedding_model, call_kwargs={"show_progress_bar": False}
) 
```

If you would like to use a higher-dimensional model, here are some possible alternatives you could use instead:

- mixedbread-ai/mxbai-embed-large-v1
- avsolatorio/GIST-Embedding-v0

For other possible choices, take a look at the [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) managed by HuggingFace.


### Local LLM Deployment

Due to its size and performance it is best to run the `Mistral 7B` LLM. Here you would deploy it as a service running on GPU, using `Ollama`.

To run local LLM, you can refer to these steps:
- Download Ollama from [ollama.com/download](https://ollama.com/download)
- In your terminal, run `ollama serve`
- In another terminal, run `ollama run mistral`

You can now test it with the following request:

```bash
curl -X POST http://localhost:11434/api/generate -d '{
  "model": "mistral",
  "prompt":"Here is a story about llamas eating grass"
 }'
```


### LLM Initialization

Now you will initialize the LLM instance that will call the local model.

```python
model = LiteLLMChat(
    model="ollama/mistral",
    temperature=0,
    top_p=1,
    api_base="http://localhost:11434",  # local deployment
    format="json",  # only available in Ollama local deploy, do not use in Mistral API
)
```

## Running the app

First, make sure your local LLM is up and running. By default, the pipeline tries to access the LLM at `http://localhost:11434`. You can change that by setting `LLM_API_BASE` environmental variable or creating `.env` file which sets its value.

### With Docker
In order to let the pipeline get updated with each change in local files, you need to mount the folder onto the docker. The following commands show how to do that.

```bash
# Build the image in this folder
docker build -t privaterag .

# Run the image, mount the `data` folder into image 
# -e is used to pass value of LLM_API_BASE environmental variable
docker run -v ./data:/app/data -e LLM_API_BASE -p 8000:8000 privaterag
```

### Locally
To run locally you need to install the Pathway app with LLM dependencies using:
```bash
pip install pathway[all]
```

Then change your directory in the terminal to this folder and run the app:
```bash
python app.py
```

## Querying the app/pipeline

Finally, query the application with;

```bash
curl -X 'POST'   'http://0.0.0.0:8000/v1/pw_ai_answer'   -H 'accept: */*'   -H 'Content-Type: application/json'   -d '{
  "prompt": "What is the start date of the contract?" 
}'
```
> `December 21, 2015 [6]`


## Modifying the code

Under the main function, we define:
- input folders
- LLM
- embedder
- index
- host and port to run the app
- run options (caching, cache folder)

By default, we used locally deployed `Mistral 7B`. App is LLM agnostic and, it is possible to use any LLM.
You can modify any of the components by checking the options from the imported modules: `from pathway.xpacks.llm import embedders, llms, parsers, splitters`.

It is also possible to easily create new components by extending the [`pw.UDF`](https://pathway.com/developers/user-guide/data-transformation/user-defined-functions) class and implementing the `__wrapped__` function.


## Conclusion:

Now you have a fully private RAG set up with Pathway and Ollama. All your data remains safe on your system. Moreover, the set-up is optimized for speed, thanks to how Ollama runs the LLM, and how Pathway’s adaptive retrieval mechanism reduces token consumption while preserving the accuracy of the RAG.

This is a full production-ready set-up which includes reading your data sources, parsing the data, and serving the endpoint.
This private RAG setup can be run entirely locally with open-source LLMs, making it ideal for organizations with sensitive data and explainable AI needs.

## Quick Links:

- [Pathway Developer Documentation](https://pathway.com/developers/user-guide/introduction/welcome)
- [Pathway App Templates](https://pathway.com/developers/templates)
- [Discord Community of Pathway](https://discord.gg/pathway)
- [Pathway Issue Tracker](https://github.com/pathwaycom/pathway/issues)
- [End-to-end dynamic RAG pipeline with Pathway](https://github.com/pathwaycom/llm-app/tree/main/examples/pipelines/demo-question-answering)
- [Using Pathway as a vector store with Langchain](https://python.langchain.com/v0.2/docs/integrations/vectorstores/pathway/) 
- [Using Pathway as a retriever with LlamaIndex](https://docs.llamaindex.ai/en/stable/examples/retrievers/pathway_retriever/) 

Make sure to drop a “Star” to our repositories if you found this resource helpful!
