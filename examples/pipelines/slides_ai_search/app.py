import base64
import logging
import os

import pathway as pw
from dotenv import load_dotenv
from pathway.udfs import DiskCache, ExponentialBackoffRetryStrategy
from pathway.xpacks.llm import embedders, llms
from pathway.xpacks.llm.parsers import SlideParser
from pathway.xpacks.llm.question_answering import DeckRetriever
from pathway.xpacks.llm.vector_store import SlidesVectorStoreServer
from pydantic import BaseModel
from utils import get_model_from_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,  # instructor library overrides `basicConfig`, this fixes logging
)

IMAGE_DUMP_FOLDER = "storage/pw_dump_images"
FILE_DUMP_FOLDER = "storage/pw_dump_files"


def encode_str(original_string: str) -> str:
    return base64.urlsafe_b64encode(original_string.encode("utf-8")).decode("utf-8")


def add_slide_id(text: str, metadata: dict) -> tuple[str, dict]:
    # encode url-safe filename. remove `_` chars to use them as the page separator.
    encoded_name = encode_str(metadata["path"].split("/")[-1]).replace("_", "-")

    page = metadata["image_page"]
    page_count = metadata["tot_pages"]

    slide_id = f"{encoded_name}_{page}_{page_count}.png"

    logging.info(f"`add_slide_id` for {slide_id}...")

    metadata["slide_id"] = slide_id

    return (text, metadata)


def dump_img_callback(key, row, time, is_addition):
    # save images parsed by the Pathway
    metadata = row["data"]
    with open(f"{IMAGE_DUMP_FOLDER}/{metadata['slide_id'].value}", "wb") as f:
        f.write(base64.b64decode(metadata["b64_image"].value))


def dump_file_callback(key, row, time, is_addition):
    # save parsed files
    file_name = row["path"].value.split("/")[-1]
    with open(f"{FILE_DUMP_FOLDER}/{file_name}", "wb") as f:
        f.write(row["data"])


if __name__ == "__main__":
    load_dotenv()

    PATHWAY_HOST = os.environ.get("PATHWAY_HOST", "0.0.0.0")
    PATHWAY_PORT = int(os.environ.get("PATHWAY_PORT", 8000))

    SEARCH_TOPK = int(os.environ.get("SEARCH_TOPK", 6))

    os.makedirs(IMAGE_DUMP_FOLDER, exist_ok=True)
    os.makedirs(FILE_DUMP_FOLDER, exist_ok=True)

    pydantic_schema: type[BaseModel] | None = None
    schema_file = os.environ.get("SCHEMA_FILE_PATH")

    if schema_file:
        pydantic_schema = get_model_from_file(schema_file)

    path = "./data/"

    folder = pw.io.fs.read(
        path=path,
        format="binary",
        with_metadata=True,
    )

    # folder = pw.io.gdrive.read(
    #     object_id=<GDRIVE_OBJ_ID>,
    #     with_metadata=True,
    #     service_user_credentials_file="secrets.json",
    #     refresh_interval=30,
    #     object_size_limit=None,
    #     name_pattern="*.pdf",
    # )

    sources = [
        folder,
    ]  # list of input sources

    chat = llms.OpenAIChat(
        model="gpt-4o",
        retry_strategy=ExponentialBackoffRetryStrategy(
            max_retries=6, initial_delay=2500, backoff_factor=2.5
        ),
        cache_strategy=DiskCache(),
        temperature=0.0,
        capacity=3,  # reduce this in case you are hitting API throttle limits
    )

    parser = SlideParser(
        detail_parse_schema=pydantic_schema,
        run_mode="parallel",
        include_schema_in_text=False,
        llm=chat,
    )
    embedder = embedders.OpenAIEmbedder(cache_strategy=DiskCache())

    doc_store = SlidesVectorStoreServer(
        *sources,
        embedder=embedder,
        splitter=None,
        parser=parser,
        doc_post_processors=[add_slide_id],
    )

    app = DeckRetriever(
        llm=chat,
        indexer=doc_store,
        search_topk=SEARCH_TOPK,
    )

    chunked_docs = app.indexer._graph["chunked_docs"]

    m_table = chunked_docs.select(
        data=pw.this.data["metadata"],
    )

    pw.io.subscribe(m_table, on_change=dump_img_callback)

    docs = app.indexer._graph["docs"]

    t = docs.select(data=docs.data, path=docs._metadata["path"])
    pw.io.subscribe(t, on_change=dump_file_callback)

    app.build_server(host=PATHWAY_HOST, port=PATHWAY_PORT)

    app.run_server(with_cache=True, terminate_on_error=False)
