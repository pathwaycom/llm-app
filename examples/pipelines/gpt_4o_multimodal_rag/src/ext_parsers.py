# Copyright © 2024 Pathway

"""
Sneak peak on what is coming to Pathway on the next release.
"""

import logging
from io import BytesIO

import pathway as pw
from pathway.internals import udfs
from pathway.optional_import import optional_imports

logger = logging.getLogger(__name__)


class OpenParse(pw.UDF):
    """
    Parse document using `https://github.com/Filimoa/open-parse <https://github.com/Filimoa/open-parse>`_.

    `parsing_algorithm` can be one of `llm`, `unitable`, `pymupdf`, `table-transformers`.
    While using in the VectorStoreServer, splitter can be set to `None` as OpenParse already chunks the documents.


    Args:
        - table_args: dict containing the table parser arguments.
        - cache_strategy: Defines the caching mechanism. To enable caching,
            a valid `CacheStrategy` should be provided.
            See `Cache strategy <https://pathway.com/developers/api-docs/udfs#pathway.udfs.CacheStrategy>`_
            for more information. Defaults to None.
    """

    def __init__(
        self,
        table_args: dict = {"parsing_algorithm": "llm"},
        cache_strategy: udfs.CacheStrategy | None = None,
    ):
        with optional_imports("xpack-llm"):
            import openparse  # noqa:F401
            from pypdf import PdfReader  # noqa:F401

            from ._parser_utils import CustomDocumentParser

        super().__init__(cache_strategy=cache_strategy)

        self.doc_parser = CustomDocumentParser(table_args=table_args)

        self.kwargs = dict(table_args=table_args)

    def __wrapped__(self, contents: bytes) -> list[tuple[str, dict]]:
        import openparse
        from pypdf import PdfReader

        reader = PdfReader(stream=BytesIO(contents))
        doc = openparse.Pdf(file=reader)

        parsed_content = self.doc_parser.parse(doc)
        nodes = [i for i in parsed_content.nodes]

        logger.info(
            f"OpenParser completed parsing, total number of nodes: {len(nodes)}"
        )

        metadata: dict = {}
        docs = list(map(lambda x: (x.dict()["text"], metadata), nodes))

        return docs
