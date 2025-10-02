# libs/cast/query/src/casting/cast/query/rag/api.py
from __future__ import annotations
from typing import Optional, List
import os
from pathlib import Path

from casting.cast.query.rag.embeddings import EmbeddingProvider, GeminiEmbeddingProvider, FakeDeterministicEmbedding
from casting.cast.query.rag.indexer import build_or_update_index
from casting.cast.query.rag.chroma_store import ChromaStore, QueryHit, ChromaEmbeddingWrapper
from casting.cast.core import CastConfig

import ruamel.yaml


def _find_root_and_vault() -> tuple[Path, Path, CastConfig]:
    cast_folder = os.environ.get("CAST_FOLDER", "").strip()
    if not cast_folder:
        raise FileNotFoundError("CAST_FOLDER env var is not set")
    vault_path = Path(cast_folder).expanduser().resolve()
    root = vault_path.parent
    cfg_path = root / ".cast" / "config.yaml"
    y = ruamel.yaml.YAML()
    cfg = CastConfig(**y.load(cfg_path.read_text(encoding="utf-8")))
    return root, vault_path, cfg


def index_cast(
    *,
    db_path: Optional[Path] = None,
    embedder: Optional[EmbeddingProvider] = None,
    cleanup_orphans: bool = True,
) -> dict:
    """Build or update the on-disk vector index for the cast pointed to by CAST_FOLDER."""
    report = build_or_update_index(
        root_path=None,
        vault_path=None,
        db_path=db_path,
        embedder=embedder or GeminiEmbeddingProvider(),
        cleanup_orphans=cleanup_orphans,
    )
    return report.__dict__


def _get_store(db_path: Optional[Path] = None) -> ChromaStore:
    root, vault, cfg = _find_root_and_vault()
    import re
    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", cfg.cast_name)
    name = f"cast_{safe_name}"
    return ChromaStore(root, name, db_path=db_path)


def search(query: str, *, top_k: int = 6, db_path: Optional[Path] = None) -> List[QueryHit]:
    store = _get_store(db_path=db_path)
    return store.search(query, k=top_k)


def answer(
    question: str,
    *,
    top_k: int = 6,
    db_path: Optional[Path] = None,
    model: str = None,
) -> dict:
    """
    Simple RAG answer: retrieve top_k chunks and (optionally) call a chat model.
    Defaults to returning retrieved chunks if no model is provided.
    """
    hits = search(question, top_k=top_k, db_path=db_path)
    if not model:
        return {
            "question": question,
            "hits": [h.__dict__ for h in hits],
        }

    # Use LiteLLM to summarize (allow either Gemini or OpenAI models).
    try:
        from litellm import completion  # type: ignore
    except Exception:
        return {
            "question": question,
            "hits": [h.__dict__ for h in hits],
            "note": "LiteLLM not available; returning top hits only.",
        }

    ctx = "\n\n".join(
        f"[{i+1}] {h.metadata.get('relpath')} — {h.text}"
        for i, h in enumerate(hits)
    )
    prompt = (
        "You are a helpful assistant answering from a set of notes.\n\n"
        "Cite filenames in brackets when you use them, e.g. [Notes/Foo.md].\n\n"
        f"CONTEXT:\n{ctx}\n\n"
        f"QUESTION: {question}\n\n"
        "ANSWER:"
    )
    resp = completion(model=model, messages=[{"role": "user", "content": prompt}])
    text = (resp.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
    return {"question": question, "answer": text, "hits": [h.__dict__ for h in hits]}