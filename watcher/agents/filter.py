from functools import lru_cache

class SmartFilter:
    
    def __init__(self, topics, threshold=0.30, config=None):
        self.config = config or {}
        self.threshold = threshold
        self.model = self._load_model()
        # Support both old format (string) and new format (dict with name+description)
        self.topics = []
        self.topic_texts = {}
        for t in topics:
            if isinstance(t, dict):
                name = t['name']
                desc = t.get('description', name)
                self.topics.append(name)
                self.topic_texts[name] = desc
            else:
                self.topics.append(t)
                self.topic_texts[t] = t
    
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
            # Find the rich description for this topic
            topic_text = topic
            if topic in self.topic_texts:
                topic_text = self.topic_texts[topic]
            
            text = self.get_article_text(article)
            if not text:
                return 0.0
            import numpy as np
            art_emb = self.model.encode([text])
            topic_emb = self.model.encode([topic_text])
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
        # NEW: Check for forced topic from feed configuration
        forced = article.get('forced_topic')
        if forced:
            if forced == topic:
                return True, 1.0, 'forced_override'
            else:
                return False, 0.0, 'forced_excluded'

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
            # Evaluate all methods and take the highest base score
            title = (article.get('title', '') or '').lower()
            topic_words = [
                w.lower() for w in topic.split() 
                if len(w) > 2
            ]
            title_match = any(w in title for w in topic_words)
            kw_score = self.keyword_score(article, topic)
            sem_score = self.semantic_score(article, topic)
            combined = (kw_score * 0.6) + (sem_score * 0.4)
            
            best_score = combined
            method = 'combined'
            
            if sem_score > best_score:
                best_score = sem_score
                method = 'semantic'
            if kw_score > best_score:
                best_score = kw_score
                method = 'keyword'
            if title_match and 0.9 > best_score:
                best_score = 0.9
                method = 'title_keyword'
                
            final_score = best_score

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

        config_obj = getattr(self, 'config', {}) or {}
        if config_obj.get("enable_trending_weighting", False) and len(matched) > 0:
            import datetime
            import numpy as np
            
            # Step 1: Calculate "Hotness" (Density of similar articles)
            # A simple approach: count how many other articles in 'matched' share significant words in the title.
            for i, art in enumerate(matched):
                hotness_bonus = 0.0
                title_words_i = set(w.lower() for w in art.get('title', '').split() if len(w) > 3)
                
                if title_words_i:
                    similar_count = 0
                    for j, other_art in enumerate(matched):
                        if i != j:
                            title_words_j = set(w.lower() for w in other_art.get('title', '').split() if len(w) > 3)
                            overlap = len(title_words_i.intersection(title_words_j))
                            if overlap >= 2: # At least 2 significant words overlap
                                similar_count += 1
                    
                    # Add up to 0.5 bonus if many sources reported the same event
                    hotness_bonus = min(0.5, similar_count * 0.1)

                # Step 2: Calculate "Recency" (Time decay)
                recency_bonus = 0.0
                pub_date_str = art.get('published', '')
                if pub_date_str:
                    from email.utils import parsedate_to_datetime
                    pub_date = None
                    # Attempt RFC 822 format (Standard RSS)
                    try:
                        pub_date = parsedate_to_datetime(pub_date_str)
                    except (TypeError, ValueError):
                        # Fallback to ISO format (Atom/JSON)
                        try:
                            import datetime
                            pub_date = datetime.datetime.fromisoformat(pub_date_str.replace('Z', '+00:00')[:19])
                        except Exception:
                            pass
                    
                    if pub_date:
                        now = datetime.datetime.utcnow()
                        # Make pub_date timezone-naive for delta calc
                        pub_date = pub_date.replace(tzinfo=None)
                        days_old = (now - pub_date).days
                        
                        if days_old <= 1:
                            recency_bonus = 0.4  # Very fresh!
                        elif days_old <= 3:
                            recency_bonus = 0.2  # Somewhat fresh
                        elif days_old > 14:
                            recency_bonus = -0.2 # Penalty for old news
                
                # Apply modifiers
                old_score = art.get('relevance_score', 0.0)
                new_score = old_score + hotness_bonus + recency_bonus
                
                # Tag it for debug/UI transparency
                if hotness_bonus > 0 or recency_bonus > 0:
                    art['trending_algorithm'] = f"+{hotness_bonus:.1f} Hot, +{recency_bonus:.1f} Fresh"
                    print(f"      [🔥 TRENDING] '{art.get('title', '')[:40]}...' boosted by +{hotness_bonus:.1f} Hot, +{recency_bonus:.1f} Fresh")
                    
                art['relevance_score'] = new_score

            # Re-sort after applying Trending/Recency weights
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
