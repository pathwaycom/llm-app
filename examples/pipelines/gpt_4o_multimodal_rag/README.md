<p align="left">
  <a href="https://pathway.com/developers/user-guide/deployment/gcp-deploy" style="display: inline-flex; align-items: center;">
    <img src="https://www.gstatic.com/pantheon/images/welcome/supercloud.svg" alt="GCP Logo" height="1.2em"> <span style="margin-left: 5px;">Deploy with GCP</span>
  </a> | 
  <a href="https://pathway.com/developers/user-guide/deployment/render-deploy" style="display: inline-flex; align-items: center;">
    <img src="../../../assets/render.png" alt="Render Logo" height="1.2em"> <span style="margin-left: 5px;">Deploy with Render</span>
  </a>
</p>

# Multimodal RAG with Pathway: Process your Financial Reports and Tables with GPT-4o

Get started with multimodal RAG using `GPT-4o` and Pathway. This showcase demonstrates how you can launch a document processing pipeline that utilizes `GPT-4o` in the parsing stage. Pathway extracts information from unstructured financial documents in your folders, updating results as documents change or new ones arrive. 

Using this approach, you can make your AI application run in permanent connection with your drive, in sync with your documents which include visually formatted elements: tables, charts, etc. 

We specifically use `GPT-4o` to improve the table data extraction accuracy and demonstrate how this approach outperforms the industry-standard RAG toolkits.

In this showcase, we focused on the finance domain because financial documents often rely heavily on tables in various forms. This showcase highlights the limitations of traditional RAG setups, which struggle to answer questions based on table data. By contrast, our multimodal RAG approach excels in extracting accurate information from tables.

## Using the service

Follow the [steps below](#running-the-app) to set up the service. This will create a REST endpoint on your selected host and port, running a service that is connected to your file folder, and ready to answer your questions. There are no extra dependencies.

In this demo, we run the service on localhost (`0.0.0.0:8000`). You can connect your own front end or application to this endpoint. Here, we test the service with `curl`.

First, let's check the files contained in your folder are currently indexed:
```bash
curl -X 'POST'   'http://0.0.0.0:8000/v1/pw_list_documents'   -H 'accept: */*'   -H 'Content-Type: application/json'
```

This will return the list of files e.g. if you start with the [data folder](./data) provided in the demo, the answer will be as follows:
> `[{"modified_at": 1715765613, "owner": "berke", "path": "data/20230203_alphabet_10K.pdf", "seen_at": 1715768762}]`

In the default app setup, the connected folder is a local file folder. You can add more folders and file sources, such as [Google Drive](https://pathway.com/developers/user-guide/connectors/gdrive-connector/#google-drive-connector) or [Sharepoint](https://pathway.com/developers/user-guide/connecting-to-data/connectors/#tutorials), by adding a line of code to the template.

If you now add or remove files from your connected folder, you can repeat the request and see the index file list has been updated automatically. You can look into the logs of the service to see the progress of the indexing of new and modified files. PDF files of 100 pages should normally take under 10 seconds to sync, and the indexing parallelizes if multiple files are added at a single time.

Now, let's ask a question from one of the tables inside the report. In our tests, regular RAG applications struggled with the tables and couldn't answer to this question correctly.

```bash
curl -X 'POST'   'http://0.0.0.0:8000/v1/pw_ai_answer'   -H 'accept: */*'   -H 'Content-Type: application/json'   -d '{
  "prompt": "How much was Operating lease cost in 2021?" 
}'
```
> `$2,699 million`

This response was correct thanks to the initial LLM parsing step. 
When we check the context that is sent to the LLM, we see that Pathway included the table in the context where as other RAG applications failed to include the table.

The following GIF shows a snippet from our experiments:

![Regular RAG vs Pathway Multimodal comparison](gpt4o_with_pathway_comparison.gif)

Let's try another one,

```bash
curl -X 'POST'   'http://0.0.0.0:8000/v1/pw_ai_answer'   -H 'accept: */*'   -H 'Content-Type: application/json'   -d '{
  "prompt": "What is the operating income for the fiscal year of 2022?" 
}'
```
> `$74,842 million`

Another example, let's ask a question that can be answered from the table on the 48th page of the PDF.

```bash
curl -X 'POST'   'http://0.0.0.0:8000/v1/pw_ai_answer'   -H 'accept: */*'   -H 'Content-Type: application/json'   -d '{
  "prompt": "How much was Marketable securities worth in 2021 in the consolidated balance sheets?"                                              
}'
```
> `$118,704 million`

Looking good!

## Architecture

We use `GPT-4o` in two separate places in the flow of data:
- Extracting and understanding the tables inside the PDF
- Answering questions with the retrieved context

![Architecture](gpt4o.gif)

We will use the `BaseRAGQuestionAnswerer` class provided under `pathway.xpacks` to get started on our RAG application with minimal overhead. This module brings together the foundational building bricks for the RAG application. 

It includes ingesting the data from the sources, calling the LLM, parsing and chunking the documents, creating and querying the database (index) and also serving the app on an endpoint. 

For more advanced RAG options, make sure to check out [rerankers](https://pathway.com/developers/api-docs/pathway-xpacks-llm/rerankers) and the [adaptive rag example](../adaptive-rag/).


## Running the app

> Note: Recommended way of running the Pathway on Windows is Docker, refer to [Running with the Docker section](#with-docker).

First, make sure to install the requirements by running:
```bash
pip install -r requirements.txt -U
```
Then, create a `.env` file in this directory and put your API key with `OPENAI_API_KEY=sk-...`, or add the `api_key` argument to `OpenAIChat` and `OpenAIEmbedder`. 

Then, simply run with `python app.py` in this directory.

### With Docker

First, make sure to have your OpenAI API key in the environment, you can create a `.env` file as mentioned above, or specify the `api_key` argument in the `OpenAIChat` and `OpenAIEmbedder`. 

In order to let the pipeline get updated with each change in local files, you need to mount the `data` folder inside the docker. The following commands show how to do that.

The following commands will:
- mount the `data` folder inside the Docker
- build the image
- run the app and expose the port `8000`.

You can omit the ```-v `pwd`/data:/app/data``` part if you are not using local files as a data source. 

```bash
# Make sure you are in the right directory.
cd examples/pipelines/gpt_4o_multimodal_rag/

# Build the image in this folder
docker build -t rag .

# Run the image, mount the `data` folder into image and expose the port `8000`
docker run -v `pwd`/data:/app/data -p 8000:8000 rag
```

## Modifying the code

In the main function of `app.py`, we define:
- input folders
- LLM
- embedder
- index
- host and port to run the app
- run options (caching, cache folder)

You can modify any of the components by checking the options from the imported modules: `from pathway.xpacks.llm import embedders, llms, parsers, splitters`.

It is also possible to easily create new components by extending the [`pw.UDF`](https://pathway.com/developers/user-guide/data-transformation/user-defined-functions) class and implementing the `__wrapped__` function.


## Conclusion

This showcase demonstrates setting up a powerful RAG pipeline with advanced table parsing capabilities, unlocking new finance use cases. While we've only scratched the surface, there's more to explore:

- Re-ranking: Prioritize the most relevant results for your specific query.
- Knowledge graphs: Leverage relationships between entities to improve understanding.
- Hybrid indexing: Combine different indexing strategies for optimal retrieval.
- Adaptive reranking: Iteratively enlarge the context for optimal accuracy, see [our example](../adaptive-rag/README.md).
Stay tuned for future examples exploring these advanced techniques with Pathway!

RAG applications are most effective when tailored to your specific use case. Here's how you can customize yours:

- Document parsers and splitters: Fine-tune how documents are processed and broken down for analysis.
- Indexing and retrieval strategies: Choose the most efficient approach for your data and search needs.
- User Interface (UI): Design a user-friendly interface that caters to your end users' workflows.

Ready to Get Started? 

Let's discuss how we can help you build a powerful, customized RAG application. [Reach us here to talk or request a demo!](https://pathway.com/solutions/enterprise-generative-ai?modal=requestdemo)
