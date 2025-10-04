# libs/cast/query/src/casting/cast/query/rag/__main__.py
from __future__ import annotations
import argparse
from pathlib import Path

from casting.cast.query.rag.api import index_cast, search
from casting.cast.query.rag.embeddings import FakeDeterministicEmbedding, GeminiEmbeddingProvider


def main():
    p = argparse.ArgumentParser("cast-rag")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_index = sub.add_parser("index", help="Build or update the vector index")
    p_index.add_argument("--fake", action="store_true", help="Use fake embeddings (offline)")

    p_search = sub.add_parser("search", help="Search the index")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("-k", "--top-k", type=int, default=6)

    args = p.parse_args()

    if args.cmd == "index":
        embedder = FakeDeterministicEmbedding() if args.fake else GeminiEmbeddingProvider()
        rep = index_cast(embedder=embedder, cleanup_orphans=True)
        print("Index report:", rep)
    elif args.cmd == "search":
        hits = search(args.query, top_k=args.top_k)
        for i, h in enumerate(hits, 1):
            print(f"\n[{i}] score={h.score:.3f} {h.metadata.get('relpath')} (id={h.metadata.get('file_id')})")
            print(h.text[:500].strip().replace("\n", " ") + ("…" if len(h.text) > 500 else ""))


if __name__ == "__main__":
    main()