# libs/cast/query/src/casting/cast/query/rag/chroma_store.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple
import os
from pathlib import Path

import chromadb
from chromadb.config import Settings


DEFAULT_DB_SUBDIR = ".cast/chroma"


class ChromaEmbeddingWrapper:
    """Wrapper to make our EmbeddingProvider compatible with ChromaDB."""

    def __init__(self, embedding_provider):
        self.embedding_provider = embedding_provider

    def __call__(self, input):
        if isinstance(input, str):
            input = [input]
        return self.embedding_provider.embed_texts(input)

    def name(self):
        return f"custom_{type(self.embedding_provider).__name__}"

    def is_legacy(self):
        return False


@dataclass
class QueryHit:
    id: str
    score: float
    text: str
    metadata: Dict[str, Any]


class ChromaStore:
    """
    Chroma persistent storage wrapper.
    """

    def __init__(self, root_path: Path, collection_name: str, db_path: Optional[Path] = None, embedding_function=None):
        self.root_path = root_path
        if db_path is None:
            db_path = root_path / DEFAULT_DB_SUBDIR
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(db_path))
        self.collection = self.client.get_or_create_collection(name=collection_name, embedding_function=embedding_function)

    # ---------- Admin / utility ----------

    def get_file_records(self, file_id: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Return (ids, metadatas) for existing chunks of a given file id."""
        got = self.collection.get(where={"file_id": file_id}, include=["metadatas"])
        return got.get("ids", []), got.get("metadatas", [])

    def delete_ids(self, ids: Iterable[str]) -> None:
        ids = list(ids)
        if ids:
            self.collection.delete(ids=ids)

    def upsert(
        self,
        ids: List[str],
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None,
    ) -> None:
        self.collection.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)

    def update_metadatas(self, ids: List[str], metadatas: List[Dict[str, Any]]) -> None:
        # Chroma supports update with just metadatas (no embeddings)
        self.collection.update(ids=ids, metadatas=metadatas)

    def cleanup_orphans(self, valid_file_ids: set[str]) -> int:
        """Remove records for files no longer present locally."""
        got = self.collection.get(include=["metadatas"])
        ids = got.get("ids", []) or []
        metas = got.get("metadatas", []) or []

        to_delete: List[str] = []
        for i, md in enumerate(metas):
            fcid = (md or {}).get("file_id")
            if fcid and fcid not in valid_file_ids:
                to_delete.append(ids[i])
        if to_delete:
            self.collection.delete(ids=to_delete)
        return len(to_delete)

    # ---------- Query ----------

    def search(self, query: str, k: int = 6, query_embeddings: Optional[List[List[float]]] = None) -> List[QueryHit]:
        if query_embeddings:
            # Use provided embeddings (manual query)
            res = self.collection.query(query_embeddings=query_embeddings, n_results=k, include=["documents", "metadatas", "distances"])
        else:
            # Use ChromaDB's built-in embedding function
            res = self.collection.query(query_texts=[query], n_results=k, include=["documents", "metadatas", "distances"])
        ids = (res.get("ids") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        out: List[QueryHit] = []
        for i in range(len(ids)):
            # Convert Chroma distance to similarity score (lower is closer for cosine)
            dist = dists[i] if i < len(dists) else None
            score = float(1.0 - (dist or 0.0))
            out.append(QueryHit(id=ids[i], text=docs[i], metadata=metas[i], score=score))
        return out