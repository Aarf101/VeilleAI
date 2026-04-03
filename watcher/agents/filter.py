from functools import lru_cache

class SmartFilter:
    
    def __init__(self, topics, threshold=0.30, config=None):
        self.topics = topics
        self.threshold = threshold
        self.config = config or {}
        self.model = self._load_model()
    
    @staticmethod
    @lru_cache(maxsize=1)
    def _load_model():
        try:
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            print("WARNING: sentence-transformers not installed. Using local embedding fallback.")
            class DummyModel:
                def __init__(self):
                    from watcher.nlp.embeddings import EmbeddingProvider
                    self.prov = EmbeddingProvider()
                def encode(self, texts):
                    return self.prov.embed(texts)
            return DummyModel()
    
    def get_article_text(self, article):
        title   = article.get('title', '') or ''
        summary = article.get('summary', '') or ''
        desc    = article.get('description', '') or ''
        return f"{title} {summary} {desc}".lower().strip()
    
    def keyword_score(self, article, topic):
        text        = self.get_article_text(article)
        topic_words = [
            w.lower() for w in topic.split() 
            if len(w) > 2
        ]
        if not topic_words:
            return 0.0
        matches = sum(1 for w in topic_words if w in text)
        return matches / len(topic_words)
    
    def semantic_score(self, article, topic):
        try:
            text = self.get_article_text(article)
            if not text:
                return 0.0
            import numpy as np
            art_emb   = self.model.encode([text])
            topic_emb = self.model.encode([topic])
            similarity = float(np.dot(
                art_emb[0], topic_emb[0]
            ) / (
                np.linalg.norm(art_emb[0]) * 
                np.linalg.norm(topic_emb[0])
            ))
            return max(0.0, similarity)
        except:
            return 0.0
    
    def is_from_google_news_topic(self, article, topic):
        feed_url = article.get('feed_url', '') or ''
        if 'news.google.com' not in feed_url:
            return False
        import urllib.parse
        try:
            params = urllib.parse.parse_qs(
                urllib.parse.urlparse(feed_url).query
            )
            q = params.get('q', [''])[0].lower()
            return topic.lower() in q or q in topic.lower()
        except:
            return False
    
    def match_article_to_topic(self, article, topic):
        config_obj = getattr(self, 'config', {}) or {}
        blacklist = config_obj.get('topic_blacklist', [
            'smartphone', 'galaxy', 'iphone', 'samsung display',
            'electric vehicle', 'football', 'fashion', 'recipe'
        ])
        title_lower = (article.get('title', '') or '').lower()
        if any(word.lower() in title_lower for word in blacklist):
            return False, 0.0, 'blacklisted'

        if article.get('skip_filter', False):
            return True, 1.0, 'google_news_bypass'
            
        # METHOD 1: Google News pre-filtered feed
        if self.is_from_google_news_topic(article, topic):
            final_score = 1.0
            method = 'google_news'
        else:
            # METHOD 2: Direct keyword match in title
            title = (article.get('title', '') or '').lower()
            topic_words = [
                w.lower() for w in topic.split() 
                if len(w) > 2
            ]
            title_match = any(w in title for w in topic_words)
            if title_match:
                final_score = 0.9
                method = 'title_keyword'
            else:
                # METHOD 3: Keyword in full text
                kw_score = self.keyword_score(article, topic)
                if kw_score >= 0.5:
                    final_score = kw_score
                    method = 'keyword'
                else:
                    # METHOD 4: Semantic similarity
                    sem_score = self.semantic_score(article, topic)
                    if sem_score >= self.threshold:
                        final_score = sem_score
                        method = 'semantic'
                    else:
                        # Combined score check
                        combined = (kw_score * 0.6) + (sem_score * 0.4)
                        if combined >= 0.35:
                            final_score = combined
                            method = 'combined'
                        else:
                            return False, 0.0, 'rejected'

        # Apply source weight multiplication
        feed_url = article.get('feed_url', '') or article.get('source', '')
        config_obj = getattr(self, 'config', {}) or {}
        feeds_weight = config_obj.get('feeds_weight', {})
        weight = feeds_weight.get(feed_url, 1.0)
        final_score = final_score * weight

        # Final threshold check after weighting
        if final_score >= self.threshold:
            return True, final_score, method
        
        return False, 0.0, 'rejected'
    
    def filter_articles_by_topic(self, articles, topic):
        matched = []
        for article in articles:
            # We use a copy so that relevance bounds per-topic do not bleed across dictionaries
            art_copy = article.copy()
            is_match, score, method = \
                self.match_article_to_topic(art_copy, topic)
            if is_match:
                art_copy['relevance_score'] = score
                art_copy['match_method']    = method
                art_copy['matched_topic']   = topic
                matched.append(art_copy)
        
        matched.sort(
            key=lambda x: x.get('relevance_score', 0), 
            reverse=True
        )
        print(f"Topic '{topic}': "
              f"{len(matched)}/{len(articles)} articles matched")
        return matched
    
    def filter_all(self, articles):
        results = {}
        for topic in self.topics:
            matched = self.filter_articles_by_topic(
                articles, topic
            )
            results[topic] = matched
            
        total_matched = sum(len(v) for v in results.values())
        print(f"Total: {total_matched} articles matched "
              f"across {len(self.topics)} topics")
        return results
