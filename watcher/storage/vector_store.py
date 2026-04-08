"""Vector store wrapper using ChromaDB with in-memory fallback.

This provides a minimal interface for adding vectors and querying nearest
neighbors. If `chromadb` is not installed, an in-memory fallback is used
(suitable for small-scale testing only).
"""
from __future__ import annotations
from typing import List, Tuple

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except Exception:
    CHROMADB_AVAILABLE = False

import numpy as np


class VectorStore:
    def __init__(self, collection_name: str = "watcher", persist_directory: str | None = None):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        if CHROMADB_AVAILABLE:
            # Use the new Chroma client API.
            # - PersistentClient when a persist_directory is provided
            # - EphemeralClient otherwise
            if persist_directory:
                self.client = chromadb.PersistentClient(path=persist_directory)
            else:
                # In-memory client (no persistence)
                self.client = chromadb.EphemeralClient()
            # create or get collection with cosine metric
            try:
                self.col = self.client.get_collection(name=collection_name)
            except Exception:
                self.col = self.client.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            self._is_chroma = True
        else:
            self._is_chroma = False
            self._ids: List[str] = []
            self._vecs: List[np.ndarray] = []
            self._metas: List[dict] = []

    def add(self, ids: List[str], embeddings: List[List[float]], metadatas: List[dict] | None = None):
        if self._is_chroma:
            self.col.add(ids=ids, embeddings=embeddings, metadatas=metadatas)
        else:
            for i, e in zip(ids, embeddings):
                self._ids.append(i)
                self._vecs.append(np.array(e))
                self._metas.append(metadatas.pop(0) if metadatas else {})

    def query(self, embedding: List[float], n_results: int = 50) -> List[Tuple[str, float, dict]]:
        """Return list of (id, score, metadata) ordered by descending similarity."""
        if self._is_chroma:
            n_res = min(n_results, self.col.count())
            if n_res == 0:
                return []
            res = self.col.query(query_embeddings=[embedding], n_results=n_res)
            ids = res["ids"][0]
            dists = res.get("distances") and res.get("distances")[0]
            metadatas = res.get("metadatas") and res.get("metadatas")[0]
            return list(zip(ids, dists or [0] * len(ids), metadatas or [{}] * len(ids)))
        else:
            emb = np.array(embedding)
            sims = []
            for v in self._vecs:
                denom = (np.linalg.norm(emb) * np.linalg.norm(v))
                sim = float(np.dot(emb, v) / denom) if denom != 0 else 0.0
                sims.append(sim)
            idxs = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:n_results]
            return [(self._ids[i], sims[i], self._metas[i]) for i in idxs]
