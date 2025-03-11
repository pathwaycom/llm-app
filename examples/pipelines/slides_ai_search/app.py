#!/usr/bin/env python

# Copyright © 2024 Pathway

# Copied and adapted from examples/pipelines/slides_ai_search/app.py
# To use advanced features with Pathway Scale, get your free license key from
# https://pathway.com/features and paste it in the `.env` file (check `.env.example`).

from pathlib import Path
from typing import Any

import pathway as pw
from dotenv import load_dotenv
from pathway.xpacks import llm
from pathway.xpacks.llm.document_store import SlidesDocumentStore
from pathway_slides_ai_search import DeckRetrieverWithFileSave, add_slide_id, get_model
from pydantic import BaseModel, ConfigDict, FilePath, InstanceOf


class App(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000

    sources: list[InstanceOf[pw.Table]]

    llm: InstanceOf[pw.UDF]
    retriever_factory: InstanceOf[pw.indexing.AbstractRetrieverFactory]

    search_topk: int = 6

    details_schema: FilePath | dict[str, Any] | None = None

    with_cache: bool = True
    terminate_on_error: bool = False

    def run(self) -> None:
        if self.details_schema is not None:
            detail_schema = get_model(self.details_schema)
        else:
            detail_schema = None

        parser = llm.parsers.SlideParser(
            detail_parse_schema=detail_schema,
            run_mode="parallel",
            include_schema_in_text=False,
            llm=self.llm,
            cache_strategy=pw.udfs.DefaultCache(),
        )

        doc_store = SlidesDocumentStore(
            self.sources,
            retriever_factory=self.retriever_factory,
            splitter=None,
            parser=parser,
            doc_post_processors=[add_slide_id],
        )

        app = DeckRetrieverWithFileSave(
            indexer=doc_store,
            search_topk=self.search_topk,
        )

        app.build_server(host=self.host, port=self.port)

        app.run_server(
            with_cache=self.with_cache,
            terminate_on_error=self.terminate_on_error,
        )

    model_config = ConfigDict(extra="forbid")


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent

    load_dotenv(base_dir / ".env")

    with open(base_dir / "app.yaml") as f:
        config = pw.load_yaml(f)

    app = App(**config)

    app.run()
