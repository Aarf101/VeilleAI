"""Filtering agent: computes embeddings, similarity via ChromaDB, and filters items by threshold.

Primary mode: ChromaDB-based semantic similarity (recommended)
Fallback mode: Direct embedding comparison (when ChromaDB unavailable)

Functions:
- `score_item_against_topics_chromadb(item, topics, vector_store, provider)` -> float score (0-1)
- `score_item_against_topics(item, topics, provider)` -> float score (0-1) [fallback]
- `filter_items(items, topics, threshold, vector_store, provider)` -> list of (item, score, passed)
"""
from __future__ import annotations
from typing import List, Dict, Tuple, Optional

import numpy as np

from watcher.nlp.embeddings import EmbeddingProvider


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    if a is None or b is None:
        return 0.0
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)
    if a_norm == 0 or b_norm == 0:
        return 0.0
    return float(np.dot(a, b) / (a_norm * b_norm))


def _ensure_provider(provider: EmbeddingProvider | None) -> EmbeddingProvider:
    if provider is None:
        return EmbeddingProvider()
    return provider


def score_item_against_topics_chromadb(
    item: Dict, 
    topics: List[str], 
    vector_store,
    provider: EmbeddingProvider | None = None
) -> float:
    """Score item using ChromaDB semantic similarity (PREFERRED METHOD).
    
    Steps:
    1. Extract item text (content > summary > title)
    2. Encode to embedding using provider
    3. Query ChromaDB for topics: "Which topic is most similar to this item?"
    4. Return highest similarity score (0-1)
    
    Args:
        item: Dict with 'content', 'summary', or 'title' keys
        topics: List of topic strings (will be embedded and searched in ChromaDB)
        vector_store: VectorStore instance (ChromaDB wrapper)
        provider: EmbeddingProvider (will be created if None)
    
    Returns:
        float: Similarity score in [0, 1]
    """
    provider = _ensure_provider(provider)
    
    # Extract item text
    text = (item.get("content") or item.get("summary") or item.get("title") or "").strip()
    if not text:
        return 0.0
    
    # Encode item
    item_emb = provider.embed([text])[0]
    
    # Query ChromaDB for each topic: find the closest match
    max_score = 0.0
    for topic in topics:
        try:
            # Query: how similar is the item to articles about this topic?
            # We search ChromaDB with the item embedding, filter by topic metadata if stored.
            results = vector_store.query(item_emb.tolist(), n_results=5)
            if results:
                _, distance, _ = results[0]
                # Convert cosine distance to cosine similarity and clamp to [0.0, 1.0]
                similarity = 1.0 - distance
                if similarity < 0.0:
                    similarity = 0.0
                if similarity > 1.0:
                    similarity = 1.0
                max_score = max(max_score, similarity)
        except Exception:
            # If ChromaDB query fails, fall back to topic embedding comparison
            topic_emb = provider.embed([topic])[0]
            sim = _cosine_sim(item_emb, topic_emb)
            max_score = max(max_score, sim)
    
    return max_score


def compute_topic_embeddings(topics: List[str], provider: EmbeddingProvider | None = None):
    """Compute embeddings for each topic (topic can be a phrase or keywords).

    Returns numpy array of shape (n_topics, dim)
    """
    provider = _ensure_provider(provider)
    # join topic keywords if topic is list-like, but we expect strings
    texts = [t if isinstance(t, str) else " ".join(t) for t in topics]
    return provider.embed(texts)


def score_item_against_topics(item: Dict, topics: List[str], provider: EmbeddingProvider | None = None) -> float:
    """Compute the maximum cosine similarity between item text and any topic (FALLBACK).

    Item text chosen: content > summary > title.
    Returns score in [0,1].
    
    Note: This is the fallback when ChromaDB is not available.
    Prefer score_item_against_topics_chromadb() when possible.
    """
    provider = _ensure_provider(provider)
    text = (item.get("content") or item.get("summary") or item.get("title") or "").strip()
    if not text:
        return 0.0

    item_emb = provider.embed([text])[0]
    topic_embs = compute_topic_embeddings(topics, provider)

    sims = [_cosine_sim(item_emb, t) for t in topic_embs]
    if not sims:
        return 0.0
    return max(sims)


def filter_items(
    items: List[Dict], 
    topics: List[str], 
    threshold: float = 0.65, 
    vector_store=None,
    provider: EmbeddingProvider | None = None
) -> List[Tuple[Dict, float, bool]]:
    """Score and filter items using ChromaDB if available, fallback to direct embedding.

    Args:
        items: List of items to filter
        topics: List of topic strings
        threshold: Minimum score to pass filter
        vector_store: VectorStore instance (ChromaDB). If None, uses fallback method.
        provider: EmbeddingProvider (will be created if None)
    
    Returns:
        List of tuples: (item, score, passed_threshold)
    """
    provider = _ensure_provider(provider)
    
    # Use ChromaDB if available, otherwise fallback
    use_chromadb = vector_store is not None
    
    results: List[Tuple[Dict, float, bool]] = []
    for item in items:
        try:
            if use_chromadb:
                score = score_item_against_topics_chromadb(item, topics, vector_store, provider)
            else:
                score = score_item_against_topics(item, topics, provider)
        except Exception:
            # If scoring fails for any reason, score as 0 (fails threshold)
            score = 0.0
        
        passed = score >= threshold
        results.append((item, score, passed))
    
    return results
