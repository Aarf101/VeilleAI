"""Embedding provider with local (sentence-transformers) and OpenAI fallback.

Usage:
  provider = EmbeddingProvider()
  vecs = provider.embed(["text1", "text2"])  # returns numpy array
"""
from __future__ import annotations
from typing import List


class EmbeddingProvider:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize with a local sentence-transformers model. This project
        uses local, open-source embeddings only (no paid API fallbacks).

        If `sentence-transformers` is not installed, a clear ImportError is raised
        with installation instructions.
        """
        self._model_name = model_name
        try:
            from sentence_transformers import SentenceTransformer

            # Use normalized embeddings so cosine similarity is well-defined
            # and bounded in [-1, 1]. This helps keep all downstream similarity
            # scores within [0, 1] after distance → similarity conversion.
            self._model = SentenceTransformer(model_name)
            self._backend = "local"
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise ImportError(
                f"sentence-transformers is required for embeddings. Detailed error: {e}"
            ) from e

    def embed(self, texts: List[str]):
        """Return embeddings as a 2D numpy array (n_texts x dim)."""
        if not texts:
            return []
        # local backend only
        import numpy as _np
        # Normalize embeddings so cosine distance from Chroma stays in range
        # and dot products correspond to cosine similarity.
        embs = self._model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return _np.array(embs)
