<p align="left">
  <a href="https://pathway.com/developers/user-guide/deployment/gcp-deploy" style="display: inline-flex; align-items: center;">
    <img src="https://www.gstatic.com/pantheon/images/welcome/supercloud.svg" alt="GCP Logo" height="1.2em"> <span style="margin-left: 5px;">Deploy with GCP</span>
  </a> | 
  <a href="https://pathway.com/developers/user-guide/deployment/render-deploy" style="display: inline-flex; align-items: center;">
    <img src="../../../assets/render.png" alt="Render Logo" height="1.2em"> <span style="margin-left: 5px;">Deploy with Render</span>
  </a>
</p>


## End to end Adaptive RAG with Pathway

This is the accompanying code for deploying the `adaptive RAG` technique with Pathway. To understand the technique and learn how it can save tokens without sacrificing accuracy, read [our showcase](https://pathway.com/developers/templates/adaptive-rag).

To learn more about building & deploying RAG applications with Pathway, including containerization, refer to [demo question answering](../demo-question-answering/README.md).

## Introduction
This app relies on modules provided under `pathway.xpacks.llm`. 

BaseRAGQuestionAnswerer is the base class to build RAG applications with Pathway vector store and Pathway xpack components.
It is meant to get you started with your RAG application right away. 

Here, we extend the `BaseRAGQuestionAnswerer` to implement the adaptive retrieval and reply to requests in the endpoint `/v1/pw_ai_answer`. 
Since we are interested in changing the behavior and logic of the RAG, we only modify `answer` function that handles all this logic, and then replies to the post request.

`answer` function takes the `pw_ai_queries` table as the input, this table contains the prompt, and other arguments coming from the post request, see the `BaseRAGQuestionAnswerer` class and defined schemas to learn more about getting inputs with post requests.
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

To see the setup used in our work, check [the showcase](https://pathway.com/developers/templates/private-rag-ollama-mistral).

## Running the app
To run the app you need to set your OpenAI API key, by setting the environmental variable `OPENAI_API_KEY` or creating an `.env` file in this directory with line `OPENAI_API_KEY=sk-...`. If you modify the code to use another LLM provider, you may need to set a relevant API key.

### With Docker
In order to let the pipeline get updated with each change in local files, you need to mount the folder onto the docker. The following commands show how to do that.

```bash
# Build the image in this folder
docker build -t adaptiverag .

# Run the image, mount the `data` folder into image 
# -e is used to pass value of OPENAI_API_KEY environmental variable
docker run -v ./data:/app/data -e OPENAI_API_KEY -p 8000:8000 adaptiverag
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

## Using the app

Finally, query the application with;

```bash
curl -X 'POST'   'http://0.0.0.0:8000/v1/pw_ai_answer'   -H 'accept: */*'   -H 'Content-Type: application/json'   -d '{
  "prompt": "What is the start date of the contract?" 
}'
```
> `December 21, 2015 [6]`

