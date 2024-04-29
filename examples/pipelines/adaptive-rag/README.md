## End to end Adaptive RAG with Pathway

This is the accompanying code for deploying the `adaptive RAG` technique with Pathway.

To learn more about building & deploying RAG applications with Pathway, including containerization, refer to [demo question answering](../demo-question-answering/README.md).

## Introduction
This app relies on modules provided under `pathway.xpacks.llm`. 

BaseRAGQuestionAnswerer is the base class to build RAG applications with Pathway vector store and Pathway xpack components.
It is meant to get you started with your RAG application right away. 

Here, we extend the `BaseRAGQuestionAnswerer` to implement the adaptive retrieval and reply to requests in the endpoint `/v1/pw_ai_answer`. 
Since we are interested in changing the behavior and logic of the RAG, we only modify `pw_ai_query` function that handles all this logic, and then replies to the post request.

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

By default, we used OpenAI `gpt-3.5-turbo`. However, as done in the showcase, it is possible to use any LLM, including locally deployed LLMs.

If you are interested in building this app in a fully private & local setup, check out the [private RAG example](../private-rag/README.md) that uses `Mistral 7B` as the LLM with a local embedding model.

You can modify any of the used components by checking the options from: `from pathway.xpacks.llm import embedders, llms, parsers, splitters`.
It is also possible to easily create new components by extending the [`pw.UDF`](https://pathway.com/developers/user-guide/data-transformation/user-defined-functions) class and implementing the `__wrapped__` function.

To see the setup used in our work, check [the showcase](https://pathway.com/developers/showcases/private-rag-ollama-mistral).

## Running the app
If you are using the OpenAI modules, create a `.env` file in this directory and put your API key with `OPENAI_API_KEY=sk-...`, or add the `api_key` argument to `OpenAIChat` and `OpenAIEmbedder`. 

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

