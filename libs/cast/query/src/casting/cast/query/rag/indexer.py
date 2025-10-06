# libs/cast/query/src/casting/cast/query/rag/indexer.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple
import os
from pathlib import Path
from datetime import datetime

from casting.cast.core import compute_digest, extract_cast_fields
from casting.cast.core.yamlio import parse_cast_file
from casting.cast.core import CastConfig  # dataclass

from casting.cast.query.rag.embeddings import EmbeddingProvider, GeminiEmbeddingProvider
from casting.cast.query.rag.chunking import split_by_headings
from casting.cast.query.rag.chroma_store import ChromaStore, ChromaEmbeddingWrapper


@dataclass
class FileToIndex:
    file_id: str
    relpath: str
    title: str
    digest: str
    body: str  # markdown body (without YAML)
    yaml: dict  # original YAML dict


@dataclass
class IndexReport:
    added: int
    updated: int
    skipped: int
    renamed_only: int
    deleted_orphans: int
    chunks: int


def _find_cast_root_from_env() -> Tuple[Path, Path]:
    """
    Return (root_path, vault_path) from env CAST_FOLDER.
    CAST_FOLDER must point at the folder named 'Cast' (or equivalent).
    """
    cast_folder = os.environ.get("CAST_FOLDER", "").strip()
    if not cast_folder:
        raise FileNotFoundError("CAST_FOLDER env var is not set; please set it to your Cast folder path")
    vault_path = Path(cast_folder).expanduser().resolve()
    root = vault_path.parent
    if not vault_path.name.lower() == "cast":
        # Accept non-standard naming, but still treat parent as root.
        root = vault_path.parent
    # sanity
    if not (root / ".cast").exists():
        raise FileNotFoundError(f".cast directory not found under {root}")
    return root, vault_path


def _load_cast_config(root: Path) -> CastConfig:
    import ruamel.yaml

    y = ruamel.yaml.YAML()
    cfg_path = root / ".cast" / "config.yaml"
    data = y.load((cfg_path).read_text(encoding="utf-8"))
    return CastConfig(**data)


def _collection_name(cfg: CastConfig) -> str:
    # Unique per cast (cast-name is unique in your ecosystem); safe chars only.
    # Replace invalid chars for ChromaDB collection names
    import re

    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", cfg.cast_name)
    return f"cast_{safe_name}"


def _iter_files_to_index(vault_path: Path) -> Iterable[FileToIndex]:
    for md in vault_path.rglob("*.md"):
        try:
            fm, body, has_cast = parse_cast_file(md)
            if not has_cast or not isinstance(fm, dict):
                continue
            # Skip special types
            typ = (fm.get("type") or "").strip().lower()
            if typ in {"prompt", "spec"}:
                continue
            cast_fields = extract_cast_fields(fm)
            file_id = cast_fields.get("id")
            if not file_id:
                continue
            title = fm.get("title") or fm.get("name") or md.stem
            digest = compute_digest(fm, body)
            yield FileToIndex(
                file_id=file_id,
                relpath=str(md.relative_to(vault_path)),
                title=str(title),
                digest=digest,
                body=body or "",
                yaml=fm,
            )
        except Exception:
            # Best-effort: skip malformed files
            continue


def _chunks_for(body: str, title: str, max_chars: int) -> List[str]:
    # Prepend title for context (if not already included as a heading in body)
    title_line = f"# {title}".strip()
    doc = title_line + "\n\n" + (body or "")
    if len(doc) <= max_chars:
        return [doc]
    # Too large — split
    return split_by_headings(doc, max_chars=max_chars)


def build_or_update_index(
    *,
    root_path: Optional[Path] = None,
    vault_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
    embedder: Optional[EmbeddingProvider] = None,
    cleanup_orphans: bool = True,
) -> IndexReport:
    """
    Build / update the Chroma index for the current Cast.

    - Index key: file id (chunks are id::0000, id::0001, …)
    - Re-embed only when the file's digest changes
    - If only 'relpath' changes (rename), metadata is updated without re-embedding
    - Optionally remove orphans (records for files no longer present)
    """
    if root_path is None or vault_path is None:
        root_path, vault_path = _find_cast_root_from_env()
    cfg = _load_cast_config(root_path)
    collection_name = _collection_name(cfg)
    chroma_embedding_fn = ChromaEmbeddingWrapper(embedder)
    store = ChromaStore(root_path, collection_name, db_path=db_path, embedding_function=chroma_embedding_fn)

    embedder = embedder or GeminiEmbeddingProvider()

    added = updated = skipped = renamed_only = deleted_orphans = chunk_count = 0

    # Track currently present file ids
    present_ids: set[str] = set()

    for file in _iter_files_to_index(vault_path):
        present_ids.add(file.file_id)
        ids_existing, metas_existing = store.get_file_records(file.file_id)

        existing_digest_set = {m.get("digest") for m in metas_existing} if metas_existing else set()
        existing_relpaths = {m.get("relpath") for m in metas_existing} if metas_existing else set()

        # CASE A: exact digest match present -> up-to-date
        if existing_digest_set == {file.digest} and ids_existing:
            # But relpath may have changed (rename); update metadata only
            if existing_relpaths != {file.relpath}:
                new_metas = []
                for m in metas_existing:
                    m2 = dict(m or {})
                    m2["relpath"] = file.relpath
                    m2["title"] = file.title
                    new_metas.append(m2)
                store.update_metadatas(ids_existing, new_metas)
                renamed_only += 1
            else:
                skipped += 1
            continue

        # CASE B: digest changed or first time — (re)embed
        # Replace existing chunks for this file
        if ids_existing:
            store.delete_ids(ids_existing)

        chunks = _chunks_for(file.body, file.title, max_chars=embedder.max_chars)
        chunk_count += len(chunks)
        chunk_ids = [f"{file.file_id}::{i:04d}" for i in range(len(chunks))]
        metadatas = [
            {
                "file_id": file.file_id,
                "relpath": file.relpath,
                "digest": file.digest,
                "chunk_index": i,
                "title": file.title,
                "cast_name": cfg.cast_name,
            }
            for i in range(len(chunks))
        ]

        # Try to embed whole document -> we already chunked if too big, so just embed chunks
        vectors = embedder.embed_texts(chunks)

        store.upsert(ids=chunk_ids, texts=chunks, metadatas=metadatas, embeddings=vectors)
        if ids_existing:
            updated += 1
        else:
            added += 1

    if cleanup_orphans:
        deleted_orphans = store.cleanup_orphans(present_ids)

    return IndexReport(
        added=added,
        updated=updated,
        skipped=skipped,
        renamed_only=renamed_only,
        deleted_orphans=deleted_orphans,
        chunks=chunk_count,
    )
