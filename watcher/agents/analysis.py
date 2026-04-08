"""
ANALYSIS AGENT (Fixed) - Novelty detection + simple categorization

Responsibilities:
- Compare items with previous period to detect novelty
- Categorize items into predefined categories (announcement, trend, analysis, etc.)
- NO prediction, NO long-term trend analysis, NO prognosis
"""
from typing import List, Dict, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


class AnalysisAgent:
    """
    Analyzes items for:
    1. Novelty (vs. previous period only)
    2. Category assignment
    """
    
    def __init__(self, storage=None, provider=None):
        """
        Args:
            storage: Storage instance for comparing against previous period
            provider: EmbeddingProvider instance
        """
        self.storage = storage
        self.provider = provider
        
        if provider is None:
            from watcher.nlp.embeddings import EmbeddingProvider
            self.provider = EmbeddingProvider()
    
    def analyze(self, items: List[Dict], lookback_days: int = 7) -> List[Dict]:
        """
        Analyze items for novelty and categorization.
        
        Args:
            items: Filtered items to analyze
            lookback_days: How far back to compare for novelty (previous period)
            
        Returns:
            List of items with added 'category', 'novelty_score', and 'priority' fields
        """
        if not items:
            return []
        
        analyzed_items = []
        
        for item in items:
            # Check novelty against previous period
            novelty_score = self._novelty_score_vs_previous_period(item, lookback_days)
            
            # Categorize the item
            category = self._categorize(item)
            
            # Add fields to item
            item['novelty_score'] = novelty_score
            item['category'] = category
            
            # Determine priority
            relevance = item.get('relevance_score', 0.5)
            priority = self._determine_priority(novelty_score, relevance, category)
            item['priority'] = priority
            
            analyzed_items.append(item)
            
            logger.debug(f"AnalysisAgent: {item.get('title', '')[:50]} → {category} (novelty: {novelty_score:.2f}, priority: {priority})")
        
        logger.info(f"AnalysisAgent: Analyzed {len(items)} items (avg novelty: {np.mean([i.get('novelty_score', 0.5) for i in analyzed_items]):.2f})")
        
        return analyzed_items
    
    def _novelty_score_vs_previous_period(self, item: Dict, lookback_days: int) -> float:
        """
        Check novelty by comparing with previous period.
        
        Returns novelty score (0.0-1.0): higher = more novel
        Based on similarity with past items: lower similarity = higher novelty
        """
        if self.storage is None:
            logger.warning("No storage configured, assuming moderate novelty")
            return 0.7
        
        try:
            # Get items from previous period
            recent_items = self.storage.get_recent_items_full(limit=200)
            
            if not recent_items:
                return 1.0  # No history = completely novel
            
            # Embed candidate item
            text = (item.get('content') or item.get('summary') or item.get('title') or '').strip()
            if not text:
                return 0.0
            
            item_emb = self.provider.embed([text])[0]
            
            # Compare against recent items
            similarities = []
            for prev_item in recent_items:
                prev_text = (prev_item.get('content') or prev_item.get('summary') or prev_item.get('title') or '').strip()
                if not prev_text:
                    continue
                
                prev_emb = self.provider.embed([prev_text])[0]
                sim = self._cosine_sim(item_emb, prev_emb)
                similarities.append(sim)
            
            # Novelty = inverse of max similarity
            if similarities:
                max_similarity = max(similarities)
                novelty_score = 1.0 - max_similarity  # Invert: low similarity = high novelty
            else:
                novelty_score = 1.0
            
            return float(np.clip(novelty_score, 0.0, 1.0))
            
        except Exception as e:
            logger.warning(f"Novelty score calculation failed: {e}, assuming moderate")
            return 0.7
    
    def _is_novel_vs_previous_period(self, item: Dict, lookback_days: int) -> bool:
        """
        Check if item is novel by comparing with previous period only.
        
        Returns True if item has no close match in database within lookback period.
        """
        if self.storage is None:
            logger.warning("No storage configured, assuming all items are novel")
            return True
        
        try:
            # Get items from previous period
            recent_items = self.storage.get_recent_items_full(limit=200)
            
            if not recent_items:
                return True
            
            # Embed candidate item
            text = (item.get('content') or item.get('summary') or item.get('title') or '').strip()
            if not text:
                return False
            
            item_emb = self.provider.embed([text])[0]
            
            # Compare against recent items
            max_similarity = 0.0
            for prev_item in recent_items:
                prev_text = (prev_item.get('content') or prev_item.get('summary') or prev_item.get('title') or '').strip()
                if not prev_text:
                    continue
                
                prev_emb = self.provider.embed([prev_text])[0]
                sim = self._cosine_sim(item_emb, prev_emb)
                max_similarity = max(max_similarity, sim)
            
            # Novel if similarity below threshold
            novelty_threshold = 0.75
            is_novel = max_similarity < novelty_threshold
            
            return is_novel
            
        except Exception as e:
            logger.warning(f"Novelty check failed: {e}, assuming novel")
            return True
    
    def _categorize(self, item: Dict) -> str:
        """
        Simple keyword-based categorization.
        Returns one of: announcement, event, trend, analysis, regulation, other
        """
        text = (
            (item.get('title') or '') + ' ' +
            (item.get('summary') or '') + ' ' +
            (item.get('content') or '')
        ).lower()
        
        categories = {
            'announcement': ['announce', 'launch', 'release', 'unveiled', 'introduced'],
            'event': ['conference', 'summit', 'webinar', 'meetup', 'event'],
            'trend': ['trend', 'growing', 'rise', 'increasing', 'surge'],
            'analysis': ['analysis', 'study', 'research', 'report', 'paper'],
            'regulation': ['law', 'regulation', 'regulatory', 'regulation', 'act'],
        }
        
        scores = {}
        for category, keywords in categories.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[category] = score
        
        if not scores or max(scores.values()) == 0:
            return 'other'
        
        return max(scores, key=scores.get)
    
    
    def _determine_priority(self, novelty: float, relevance: float, category: str) -> str:
        """Determine priority (high, medium, low) based on novelty and relevance."""
        # Combined score
        combined = (novelty * 0.6) + (relevance * 0.4)

        # Announcements and regulations are always high priority if relevant
        if category in ["announcement", "regulation"] and combined >= 0.6:
            return "high"

        # High combined score
        if combined >= 0.75:
            return "high"

        # Medium
        if combined >= 0.5:
            return "medium"

        # Low
        return "low"
    
    @staticmethod
    def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity."""
        a_norm = np.linalg.norm(a)
        b_norm = np.linalg.norm(b)
        
        if a_norm == 0 or b_norm == 0:
            return 0.0
        
        return float(np.dot(a, b) / (a_norm * b_norm))
