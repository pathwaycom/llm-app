"""Async vector-database accessors.

Each accessor implements :class:`AsyncVectorAccessor` and knows how to fetch the
top-k nearest chunks for a query embedding from one backend. The server is
decoupled from the indexer and talks to the vector DB only through these.
"""

from serviette.server.accessors.abstract import AsyncVectorAccessor

__all__ = ["AsyncVectorAccessor", "build_accessor"]


def build_accessor(vector_db) -> AsyncVectorAccessor:
    """Construct the accessor matching a ``vector_db`` config section.

    Imports are local so installing only the backend you use (e.g. no
    ``pymilvus``) does not break the others.
    """

    db_type = vector_db.type
    if db_type == "duckdb":
        from serviette.server.accessors.duckdb import DuckDbAccessor

        return DuckDbAccessor(vector_db)
    if db_type == "pgvector":
        from serviette.server.accessors.pgvector import PgVectorAccessor

        return PgVectorAccessor(vector_db)
    if db_type == "milvus":
        from serviette.server.accessors.milvus import MilvusAccessor

        return MilvusAccessor(vector_db)
    if db_type == "qdrant":
        from serviette.server.accessors.qdrant import QdrantAccessor

        return QdrantAccessor(vector_db)
    if db_type == "chroma":
        from serviette.server.accessors.chroma import ChromaAccessor

        return ChromaAccessor(vector_db)
    if db_type == "weaviate":
        from serviette.server.accessors.weaviate import WeaviateAccessor

        return WeaviateAccessor(vector_db)
    if db_type == "pinecone":
        from serviette.server.accessors.pinecone import PineconeAccessor

        return PineconeAccessor(vector_db)
    if db_type == "mongodb":
        from serviette.server.accessors.mongodb import MongoDbAccessor

        return MongoDbAccessor(vector_db)
    raise ValueError(f"Unsupported vector_db type: {db_type!r}")
