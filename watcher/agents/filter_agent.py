"""
FILTER AGENT (Redefined) - Stateless semantic relevance scoring

Responsibilities:
- Measure relevance of items against topics using embeddings
- NO state, NO memory, NO novelty detection
- Pure function: (item, topics) → score [0, 1]
- Binary decision: relevant or not
"""
from typing import List, Dict, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FilterAgent:
    """Stateless semantic relevance filter."""
    
    def __init__(self, provider=None):
        """
        Args:
            provider: EmbeddingProvider instance (embeddings only, no state)
        """
        self.provider = provider
        if provider is None:
            from watcher.nlp.embeddings import EmbeddingProvider
            self.provider = EmbeddingProvider()
    
    def filter(self, items: List[Dict], topics: List[str], threshold: float = 0.65) -> List[Dict]:
        """
        Filter items by semantic relevance to topics.
        
        STATELESS: Each call is independent, no memory of previous results.
        
        Args:
            items: List of collected items
            topics: List of topic strings
            threshold: Minimum relevance score (0-1)
            
        Returns:
            List of items with added 'relevance_score' and 'relevant_topics' fields
        """
        if not items or not topics:
            return items
        
        # Compute topic embeddings once
        topic_embs = self._embed_topics(topics)
        
        results = []
        for item in items:
            score = self._score_item(item, topic_embs)
            
            # Add relevance score to item
            item["relevance_score"] = score
            
            # Find which topics matched
            matching_topics = self._find_matching_topics(item, topic_embs, topics)
            item["relevant_topics"] = matching_topics
            
            if score >= threshold:
                results.append(item)
        
        logger.info(f"FilterAgent: {len(results)}/{len(items)} items passed relevance threshold ({threshold})")
        return results
    
    def _find_matching_topics(self, item: Dict, topic_embs: np.ndarray, topics: List[str]) -> List[str]:
        """Find which specific topics match this item."""
        text = (item.get('content') or item.get('summary') or item.get('title') or '').strip()
        if not text:
            return []
        
        item_emb = self.provider.embed([text])[0]
        matching = []
        
        for i, topic_emb in enumerate(topic_embs):
            sim = self._cosine_sim(item_emb, topic_emb)
            if sim >= 0.5:  # Higher threshold for individual topic match
                matching.append(topics[i])
        
        return matching
    
    def _embed_topics(self, topics: List[str]) -> np.ndarray:
        """Embed all topics. Returns shape (n_topics, embedding_dim)."""
        return self.provider.embed(topics)
    
    def _score_item(self, item: Dict, topic_embeddings: np.ndarray) -> float:
        """
        Score single item against topics.
        Returns max cosine similarity (0-1).
        """
        # Extract text (prefer content → summary → title)
        text = (item.get('content') or item.get('summary') or item.get('title') or '').strip()
        
        if not text:
            return 0.0
        
        # Embed item text
        item_emb = self.provider.embed([text])[0]
        
        # Compute cosine similarities
        sims = [self._cosine_sim(item_emb, topic_emb) for topic_emb in topic_embeddings]
        
        return max(sims) if sims else 0.0
    
    @staticmethod
    def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        a_norm = np.linalg.norm(a)
        b_norm = np.linalg.norm(b)
        
        if a_norm == 0 or b_norm == 0:
            return 0.0
        
        return float(np.dot(a, b) / (a_norm * b_norm))
