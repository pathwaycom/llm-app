import logging
import os

# flake8: noqa
os.environ["TESSDATA_PREFIX"] = (
    "/usr/share/tesseract/tessdata/"  # fix for tesseract ocr
)

import pathway as pw
from dotenv import load_dotenv
from pathway.udfs import DiskCache, ExponentialBackoffRetryStrategy
from pathway.xpacks.llm import embedders, llms, prompts  # , parsers, splitters
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from pathway.xpacks.llm.vector_store import VectorStoreServer
from src.ext_parsers import OpenParse

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


if __name__ == "__main__":
    path = "./data/20230203_alphabet_10K.pdf"

    folder = pw.io.fs.read(
        path=path,
        format="binary",
        with_metadata=True,
    )

    sources = [
        folder,
    ]  # define the inputs (local folders & files, google drive, sharepoint, ...)

    chat = llms.OpenAIChat(
        model="gpt-4o",
        retry_strategy=ExponentialBackoffRetryStrategy(max_retries=6),
        cache_strategy=DiskCache(),
        temperature=0.0,
    )

    app_host = "0.0.0.0"
    app_port = 8000

    parser = OpenParse()
    embedder = embedders.OpenAIEmbedder(cache_strategy=DiskCache())

    doc_store = VectorStoreServer(
        *sources,
        embedder=embedder,
        splitter=None,  # OpenParse parser handles the chunking
        parser=parser,
    )

    app = BaseRAGQuestionAnswerer(
        llm=chat,
        indexer=doc_store,
        search_topk=6,
        short_prompt_template=prompts.prompt_qa,
    )

    app.build_server(host=app_host, port=app_port)

    app.run_server(with_cache=True, terminate_on_error=False)
