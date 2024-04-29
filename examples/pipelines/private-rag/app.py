import logging

import pathway as pw
from dotenv import load_dotenv
from pathway.xpacks.llm import embedders, llms, parsers, splitters
from pathway.xpacks.llm.question_answering import AdaptiveRAGQuestionAnswerer
from pathway.xpacks.llm.vector_store import VectorStoreServer

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


if __name__ == "__main__":
    path = "./data"

    my_folder = pw.io.fs.read(
        path=path,
        format="binary",
        with_metadata=True,
    )

    sources = [
        my_folder
    ]  # define the inputs (local folders, google drive, sharepoint, ...)

    DEFAULT_MODEL = "ollama/mistral"

    chat = llms.LiteLLMChat(
        model=DEFAULT_MODEL,
        temperature=0,
        top_p=1,
        api_base="http://localhost:11434",  # local deployment
        format="json",  # only available in Ollama local deploy, not usable in Mistral API
    )

    app_host = "0.0.0.0"
    app_port = 8000

    parser = parsers.ParseUnstructured()
    text_splitter = splitters.TokenCountSplitter(max_tokens=400)

    embedding_model = "avsolatorio/GIST-small-Embedding-v0"

    embedder = embedders.SentenceTransformerEmbedder(
        embedding_model, call_kwargs={"show_progress_bar": False}
    )

    vector_server = VectorStoreServer(
        *sources,
        embedder=embedder,
        splitter=text_splitter,
        parser=parser,
    )

    app = AdaptiveRAGQuestionAnswerer(
        llm=chat,
        indexer=vector_server,
        default_llm_name=DEFAULT_MODEL,
        n_starting_documents=2,
        factor=2,
        max_iterations=4,
        strict_prompt=True,
    )

    app.build_server(host=app_host, port=app_port)

    app.run_server(with_cache=True)
