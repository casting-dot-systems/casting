import os
from pathlib import Path
from uuid import uuid4

import ruamel.yaml

from casting.cast.query.rag.api import search
from casting.cast.query.rag.indexer import build_or_update_index
from casting.cast.query.rag.embeddings import FakeDeterministicEmbedding


def _mk_cast(tmp: Path) -> Path:
    (tmp / ".cast").mkdir(parents=True, exist_ok=True)
    (tmp / "Cast").mkdir(parents=True, exist_ok=True)

    y = ruamel.yaml.YAML()
    cfg = {"id": "search-id-" + str(uuid4()), "cast-name": "SearchCast", "cast-location": "Cast"}
    from io import StringIO
    stream = StringIO()
    y.dump(cfg, stream)
    (tmp / ".cast" / "config.yaml").write_text(stream.getvalue(), encoding="utf-8")
    return tmp / "Cast"


def _note(vault: Path, rel: str, title: str, body: str):
    y = ruamel.yaml.YAML()
    fm = {
        "title": title,
        "id": str(uuid4()),
        "cast-hsync": ["SearchCast (live)"],
    }
    from io import StringIO
    stream = StringIO()
    y.dump(fm, stream)
    content = f"---\n{stream.getvalue().strip()}\n---\n\n{body}\n"
    p = vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_retrieval(tmp_path: Path):
    vault = _mk_cast(tmp_path)
    os.environ["CAST_FOLDER"] = str(vault)

    _note(vault, "Notes/Cats.md", "Cats", "Cats hunt mice and love naps.")
    _note(vault, "Notes/Dogs.md", "Dogs", "Dogs wag tails and play fetch.")
    _note(vault, "Notes/Fish.md", "Fish", "Fish swim in water.")

    fake_embedder = FakeDeterministicEmbedding()
    build_or_update_index(embedder=fake_embedder, cleanup_orphans=True)

    # For now, manually compute query embedding and pass it
    from casting.cast.query.rag.api import _get_store
    store = _get_store()
    query_embeddings = fake_embedder.embed_texts(["tails fetch"])

    hits = store.search("tails fetch", k=3, query_embeddings=query_embeddings)
    # Ensure at least one hit and that Dogs.md ranks well under the fake embedder
    assert hits, "No hits returned"
    top_relpaths = [h.metadata.get("relpath") for h in hits]
    assert any("Dogs.md" in rp for rp in top_relpaths), f"Expected Dogs.md in top hits, got {top_relpaths}"