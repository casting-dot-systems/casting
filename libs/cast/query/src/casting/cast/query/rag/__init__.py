# libs/cast/query/src/casting/cast/query/rag/__init__.py
from casting.cast.query.rag.embeddings import EmbeddingProvider, GeminiEmbeddingProvider, FakeDeterministicEmbedding
from casting.cast.query.rag.indexer import build_or_update_index, IndexReport
from casting.cast.query.rag.api import index_cast, search, answer
from casting.cast.query.rag.chroma_store import QueryHit

__all__ = [
    "EmbeddingProvider",
    "GeminiEmbeddingProvider",
    "FakeDeterministicEmbedding",
    "build_or_update_index",
    "IndexReport",
    "index_cast",
    "search",
    "answer",
    "QueryHit",
]