"""Novelty detector and categorizer.

Provides functions to compare a candidate item to history using embeddings and
to assign a coarse category based on keyword matching.

PRIMARY MODE (ChromaDB-based):
- Uses persistent ChromaDB vector store for novelty detection
- Compares incoming articles against all stored embeddings
- Fast, scalable, persistent across runs

FALLBACK MODE (Computation-based):
- Computes embeddings on the fly for candidate and recent items
- Used when ChromaDB is unavailable
- Simple and works for small histories

Design:
- ChromaDB is the preferred method (recommended for production)
- Fallback uses the original in-memory approach
"""
from __future__ import annotations
from typing import Dict, List, Tuple, Optional
import numpy as np

from watcher.nlp.embeddings import EmbeddingProvider


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)
    if a_norm == 0 or b_norm == 0:
        return 0.0
    return float(np.dot(a, b) / (a_norm * b_norm))


def is_novel_chromadb(
    item: Dict, 
    vector_store,
    provider: EmbeddingProvider | None = None, 
    sim_threshold: float = 0.75
) -> Tuple[bool, float]:
    """Return (is_novel, max_similarity) using ChromaDB (PREFERRED METHOD).
    
    Steps:
    1. Extract item text (content > summary > title)
    2. Encode to embedding
    3. Query ChromaDB: "Find the most similar article I've seen before"
    4. If max_similarity < threshold, mark as NOVEL
    5. Otherwise, mark as DUPLICATE
    
    Args:
        item: Dict with 'content', 'summary', or 'title' keys
        vector_store: VectorStore instance (ChromaDB wrapper)
        provider: EmbeddingProvider (will be created if None)
        sim_threshold: Similarity threshold for novelty (default 0.75)
    
    Returns:
        Tuple of (is_novel: bool, max_similarity: float)
        - is_novel=True if max_similarity < sim_threshold (no similar article found)
        - is_novel=False if max_similarity >= sim_threshold (similar article exists, likely duplicate)
    """
    provider = provider or EmbeddingProvider()
    
    # Extract item text
    text = (item.get("content") or item.get("summary") or item.get("title") or "").strip()
    if not text:
        return True, 0.0
    
    # Encode item
    item_emb = provider.embed([text])[0]
    
    try:
        # Query ChromaDB: request at least 2 results so we can ignore
        # the potential self-match when the item is already stored.
        results = vector_store.query(item_emb.tolist(), n_results=5)
        
        if not results:
            # ChromaDB is empty, so this is novel
            return True, 0.0

        # Exclude self-match when possible: if multiple results are returned,
        # skip the first one and use the second as the closest "other" item.
        if len(results) > 1:
            _, distance, _ = results[1]
        else:
            _, distance, _ = results[0]

        # Convert cosine distance → cosine similarity and clamp to [0.0, 1.0]
        max_similarity = 1.0 - distance
        if max_similarity < 0.0:
            max_similarity = 0.0
        if max_similarity > 1.0:
            max_similarity = 1.0
        
        # Check novelty
        is_novel = max_similarity < sim_threshold
        
        return is_novel, max_similarity
        
    except Exception as e:
        # If ChromaDB fails, fall back to computation-based approach
        # Or mark as novel if we can't determine
        return True, 0.0


def is_novel(
    item: Dict, 
    storage, 
    provider: EmbeddingProvider | None = None, 
    sim_threshold: float = 0.75, 
    lookback: int = 200,
    vector_store=None
) -> Tuple[bool, float]:
    """Return (is_novel, max_similarity) comparing item against stored history.

    PRIMARY MODE: If vector_store (ChromaDB) is provided, uses ChromaDB
    FALLBACK MODE: Uses storage.get_recent_items_full() and computes on the fly
    
    Args:
        item: Dict with item data
        storage: Storage instance (for fallback mode)
        provider: EmbeddingProvider (will be created if None)
        sim_threshold: Similarity threshold for novelty
        lookback: Number of recent items to compare against (fallback mode only)
        vector_store: VectorStore instance (ChromaDB). If provided, uses ChromaDB.
    
    Returns:
        Tuple of (is_novel: bool, max_similarity: float)
    """
    # Use ChromaDB if available
    if vector_store is not None:
        return is_novel_chromadb(item, vector_store, provider, sim_threshold)
    
    # Fallback: computation-based novelty detection
    provider = provider or EmbeddingProvider()
    text = (item.get("content") or item.get("summary") or item.get("title") or "").strip()
    if not text:
        return True, 0.0

    # embed candidate
    cand_emb = provider.embed([text])[0]

    recent = storage.get_recent_items_full(lookback)
    if not recent:
        return True, 0.0

    # build list of contents
    texts = [ (r.get("content") or r.get("summary") or r.get("title") or "") for r in recent ]
    # embed in batches to avoid huge memory when provider supports it
    try:
        past_embs = provider.embed(texts)
    except Exception:
        # fall back to pairwise embedding
        past_embs = []
        for t in texts:
            past_embs.append(provider.embed([t])[0])
        past_embs = np.array(past_embs)

    sims = [_cosine_sim(cand_emb, p) for p in past_embs]
    max_sim = max(sims) if sims else 0.0
    return (max_sim < sim_threshold, float(max_sim))


DEFAULT_CATEGORIES = {
    "annonce": ["announce", "announced", "announce", "annonc", "lancement", "announce", "announce"],
    "événement": ["conference", "webinar", "summit", "meetup", "événement", "conférence"],
    "tendance": ["trend", "tendance", "growing", "rise", "increase"],
    "analyse": ["analysis", "analyse", "study", "report", "paper"],
    "régulation": ["law", "regulation", "regulatory", "loi", "règlement", "AI Act"],
}


def categorize_item(item: Dict, categories: Dict[str, List[str]] | None = None) -> str:
    """Assign a category based on keyword matching in title/content. Returns category key or 'autre'."""
    cats = categories or DEFAULT_CATEGORIES
    text = ((item.get("title") or "") + " \n " + (item.get("summary") or "") + " \n " + (item.get("content") or "")).lower()
    scores = {}
    for cat, kws in cats.items():
        score = 0
        for kw in kws:
            if kw.lower() in text:
                score += 1
        scores[cat] = score
    # pick max score if >0
    best = max(scores.items(), key=lambda x: x[1])
    return best[0] if best[1] > 0 else "autre"
