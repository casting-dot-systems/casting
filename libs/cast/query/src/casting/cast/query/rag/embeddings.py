# libs/cast/query/src/casting/cast/query/rag/embeddings.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable, List
import math
import re

try:
    # LiteLLM is already a dependency of cast-query
    from litellm import embedding as litellm_embedding
except Exception:  # pragma: no cover
    litellm_embedding = None


class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    max_chars: int = 32000  # conservative; model-dependent; we fall back to chunking if exceeded

    @abstractmethod
    def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        """Return an embedding vector per input text."""


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Gemini embeddings via LiteLLM.

    - Model: text-embedding-004
    - Requires: env var `GEMINI_API_KEY` or `GOOGLE_API_KEY` (LiteLLM will pick it up).
    """

    def __init__(self, model: str = "text-embedding-004", max_chars: int = 32000):
        if litellm_embedding is None:
            raise RuntimeError("LiteLLM not available; cannot initialize GeminiEmbeddingProvider")
        self.model = model
        self.max_chars = max_chars

    def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        # LiteLLM's embedding: input can be a list[str]; returns {"data":[{"embedding":[...]}...]}
        _texts = list(texts)
        if not _texts:
            return []
        resp = litellm_embedding(model=self.model, input=_texts)
        data = resp.get("data", [])
        vectors = [row.get("embedding", []) for row in data]
        if len(vectors) != len(_texts):
            raise RuntimeError("Embedding provider returned mismatched number of embeddings")
        return vectors


class FakeDeterministicEmbedding(EmbeddingProvider):
    """
    Offline, deterministic embedding for tests.
    Produces a 64-dim bag-of-characters-ish vector, normalized.

    Properties:
    - identical strings → identical vectors
    - similar strings → somewhat similar
    - works without network
    """

    def __init__(self, dim: int = 64, max_chars: int = 256):
        self.dim = dim
        self.max_chars = max_chars  # small to force chunking in tests if desired

    def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        vecs: List[List[float]] = []
        for t in texts:
            counts = [0.0] * self.dim
            # Lowercase and keep only [a-z0-9] + basic separators to stabilize.
            s = re.sub(r"[^a-z0-9 \n#]", "", (t or "").lower())
            for i, ch in enumerate(s):
                # Spread characters across dimensions
                idx = (ord(ch) + i) % self.dim
                counts[idx] += 1.0
            # L2 normalize
            norm = math.sqrt(sum(c * c for c in counts)) or 1.0
            vecs.append([c / norm for c in counts])
        return vecs