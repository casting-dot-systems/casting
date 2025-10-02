import os
import tempfile
from pathlib import Path
from uuid import uuid4

import ruamel.yaml

from casting.cast.query.rag.indexer import build_or_update_index
from casting.cast.query.rag.embeddings import FakeDeterministicEmbedding
from casting.cast.query.rag.chroma_store import ChromaStore


def _mk_cast(tmp: Path) -> Path:
    """
    Create a minimal Cast at tmp:
      tmp/.cast/config.yaml
      tmp/Cast/
    Returns vault path.
    """
    (tmp / ".cast").mkdir(parents=True, exist_ok=True)
    (tmp / "Cast").mkdir(parents=True, exist_ok=True)

    y = ruamel.yaml.YAML()
    cfg = {
        "cast-id": "test-cast-id-" + str(uuid4()),
        "cast-name": "TestCast",
        "cast-location": "Cast",
    }
    from io import StringIO
    stream = StringIO()
    y.dump(cfg, stream)
    (tmp / ".cast" / "config.yaml").write_text(stream.getvalue(), encoding="utf-8")
    return tmp / "Cast"


def _write_cast_note(vault: Path, rel: str, title: str, body: str, *, cast_id: str | None = None, extra: dict | None = None):
    p = vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    y = ruamel.yaml.YAML()
    fm = {
        "title": title,
        "cast-id": cast_id or str(uuid4()),
        "cast-hsync": ["TestCast (live)"],
        "last-updated": "2025-01-01",
    }
    if extra:
        fm.update(extra)
    from io import StringIO
    stream = StringIO()
    y.dump(fm, stream)
    front = stream.getvalue().strip()
    p.write_text(f"---\n{front}\n---\n\n{body}\n", encoding="utf-8")
    return fm["cast-id"], p


def test_index_add_update_skip_rename_and_cleanup(tmp_path: Path):
    vault = _mk_cast(tmp_path)
    os.environ["CAST_FOLDER"] = str(vault)

    # Write two notes, plus one 'spec' that must be ignored
    cid1, p1 = _write_cast_note(vault, "Notes/Cats.md", "Cats", "Cats are small carnivorous mammals.", extra=None)
    cid2, p2 = _write_cast_note(vault, "Guides/Dogs.md", "Dogs", "Dogs are domesticated mammals.", extra=None)
    cid3, p3 = _write_cast_note(vault, "Specs/Design.md", "Design", "Ignore me", extra={"type": "spec"})

    # First index build
    rep1 = build_or_update_index(embedder=FakeDeterministicEmbedding(), cleanup_orphans=True)
    assert rep1.added == 2   # 'spec' skipped
    assert rep1.updated == 0
    assert rep1.skipped in (0, 1)  # depending on chunking; ~0 here
    assert rep1.renamed_only == 0
    assert rep1.deleted_orphans == 0
    assert rep1.chunks >= 2

    # Second run without changes → skip
    rep2 = build_or_update_index(embedder=FakeDeterministicEmbedding(), cleanup_orphans=True)
    assert rep2.skipped >= 2  # both should be skipped
    assert rep2.added == 0
    assert rep2.updated == 0
    assert rep2.renamed_only == 0

    # Rename Cats.md → Knowledge/Cats.md, same digest → metadata-only update
    new_p1 = vault / "Knowledge/Cats.md"
    new_p1.parent.mkdir(parents=True, exist_ok=True)
    new_p1.write_text(p1.read_text(encoding="utf-8"), encoding="utf-8")
    p1.unlink()

    rep3 = build_or_update_index(embedder=FakeDeterministicEmbedding(), cleanup_orphans=False)
    assert rep3.renamed_only == 1

    # Modify Dogs.md → content change → updated
    p2.write_text(p2.read_text(encoding="utf-8") + "\n\nThey are great companions.\n", encoding="utf-8")
    rep4 = build_or_update_index(embedder=FakeDeterministicEmbedding(), cleanup_orphans=False)
    assert rep4.updated == 1

    # Remove Cats.md from disk → cleanup should delete orphan records
    new_p1.unlink()
    rep5 = build_or_update_index(embedder=FakeDeterministicEmbedding(), cleanup_orphans=True)
    assert rep5.deleted_orphans >= 1


def test_chunking_fallback(tmp_path: Path):
    vault = _mk_cast(tmp_path)
    os.environ["CAST_FOLDER"] = str(vault)

    long_body = "# A\n" + ("a " * 400) + "\n\n# B\n" + ("b " * 400) + "\n\n# C\n" + ("c " * 400)
    _cid, _ = _write_cast_note(vault, "Long/Long.md", "Long", long_body)

    # Fake provider with tiny max_chars to force chunking
    rep = build_or_update_index(embedder=FakeDeterministicEmbedding(max_chars=120), cleanup_orphans=True)
    assert rep.chunks >= 3  # A/B/C sections become separate chunks