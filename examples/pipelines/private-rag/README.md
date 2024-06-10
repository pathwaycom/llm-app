<p align="left">
  <a href="https://pathway.com/developers/user-guide/deployment/gcp-deploy" style="display: inline-flex; align-items: center;">
    <img src="https://www.gstatic.com/pantheon/images/welcome/supercloud.svg" alt="GCP Logo" height="1.2em"> <span style="margin-left: 5px;">Deploy with GCP</span>
  </a> | 
  <a href="https://pathway.com/developers/user-guide/deployment/render-deploy" style="display: inline-flex; align-items: center;">
    <img src="../../../assets/render.png" alt="Render Logo" height="1.2em"> <span style="margin-left: 5px;">Deploy with Render</span>
  </a>
</p>

# Fully private RAG with Pathway

This is the accompanying code for deploying the `adaptive RAG` technique with Pathway.

To learn more about building & deploying RAG applications with Pathway, including containerization, refer to [demo question answering](../demo-question-answering/README.md).

## Introduction
This app relies on modules provided under `pathway.xpacks.llm`. 

`BaseRAGQuestionAnswerer` is the base class to build RAG applications with Pathway vector store and Pathway xpack components.
It is meant to get you started with your RAG application right away. 

This example uses the `AdaptiveRAGQuestionAnswerer` that extends the `BaseRAGQuestionAnswerer` with the adaptive retrieval technique.

Then, replies to requests in the endpoint `/v1/pw_ai_answer`. 


`pw_ai_query` function takes the `pw_ai_queries` table as the input, this table contains the prompt, and other arguments coming from the post request, see the `BaseRAGQuestionAnswerer` class and defined schemas to learn more about getting inputs with post requests.
We use the data in this table to call our adaptive retrieval logic.

To do that, we use `answer_with_geometric_rag_strategy_from_index` implementation provided under the `pathway.xpacks.llm.question_answering`. 
This function takes an index, LLM, prompt and adaptive parameters such as the starting number of documents. Then, iteratively asks the question to the LLM with an increasing number of context documents retrieved from the index.
We also set `strict_prompt=True`. This adjusts the prompt with additional instructions and adds additional rails to parse the response.

We encourage you to check the implementation of `answer_with_geometric_rag_strategy_from_index`.

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

## Deploying and using a local LLM
Due to its popularity and ease of use, we decided to run the `Mistral 7B` on `Ollama`.

To run local LLM, refer to these steps:
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

## Running the app
First, make sure your local LLM is up and running.

Then, simply run with `python app.py` in this directory.
If you are interested in the Docker option, refer to [demo question answering Docker guide](../demo-question-answering/README.md#With-Docker).

## Using the app

Finally, query the application with;

```bash
curl -X 'POST'   'http://0.0.0.0:8000/v1/pw_ai_answer'   -H 'accept: */*'   -H 'Content-Type: application/json'   -d '{
  "prompt": "What is the start date of the contract?" 
}'
```
> `December 21, 2015 [6]`

