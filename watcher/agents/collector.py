"""Collector Agent - collect raw items from configured sources.

Responsibilities implemented here:
- Fetch RSS feeds and JSON APIs configured in `config.yaml`
- Extract required fields (title, published, source, url, summary/content)
- Skip obvious duplicates (same URL or same title) using storage
- Persist new items with `Storage.save_item` and return only newly inserted items
"""
from typing import List, Dict
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class CollectorAgent:
    """Collector that gathers raw items and persists deduplicated ones.

    If a `storage` instance is provided it will be used to detect duplicates and
    persist items. The method `collect_new()` returns a list of newly inserted
    items (as stored) which can then be passed to a filtering agent.
    """

    def __init__(self, storage=None, config=None):
        self.storage = storage
        self.config = config or {}

    def collect_new(self) -> List[Dict]:
        """Collect from configured feeds and APIs and return only new items.

        Returns:
            List[Dict]: newly persisted items (each dict contains at least
            `title`, `published`, `source`, `link`/`url`, `summary`/`content`).
        """
        try:
            from watcher.config import load_config
            from watcher.collectors.rss import fetch_rss
            from watcher.collectors.api import fetch_json_api
        except Exception as e:
            logger.error(f"Failed to import collectors or config: {e}")
            return []

        config = self.config or load_config() or {}
        feeds = config.get("feeds", [])
        apis = config.get("apis", [])
        max_feed = config.get("max_items_per_feed", 10)

        # Ensure we have a storage instance if we want deduplication by title/url
        if self.storage is None:
            logger.warning("CollectorAgent: no storage provided — cannot persist or dedupe by title/url")

        new_items: List[Dict] = []

        # Helper to process entries returned by collectors
        def _process_entry(entry: Dict):
            # normalize keys
            title = entry.get("title") or ""
            link = entry.get("link") or entry.get("url") or ""
            published = entry.get("published") or entry.get("fetched_at") or ""
            summary = entry.get("summary") or ""
            content = entry.get("content") or ""
            source = entry.get("source") or ""

            item = {
                "title": title,
                "link": link,
                "url": link,
                "published": published,
                "summary": summary,
                "content": content,
                "source": source,
                "fetched_at": entry.get("fetched_at"),
            }

            # YouTube Transcript Extraction Feature
            if config.get("enable_youtube_transcripts", False) and link:
                if 'youtube.com' in link or 'youtu.be/' in link:
                    try:
                        from youtube_transcript_api import YouTubeTranscriptApi
                        import urllib.parse
                        
                        video_id = None
                        if 'youtube.com/watch' in link:
                            parsed_url = urllib.parse.urlparse(link)
                            v_param = urllib.parse.parse_qs(parsed_url.query).get('v')
                            if v_param: 
                                video_id = v_param[0]
                        elif 'youtu.be/' in link:
                            video_id = link.split('youtu.be/')[1].split('?')[0]
                        elif 'youtube.com/shorts/' in link:
                            video_id = link.split('youtube.com/shorts/')[1].split('?')[0]
                        elif 'youtube.com/embed/' in link:
                            video_id = link.split('youtube.com/embed/')[1].split('?')[0]
                            
                        if video_id:
                            logger.info(f"Extracting transcript for YouTube video: {video_id}")
                            try:
                                transcript_list = YouTubeTranscriptApi.list(video_id).find_transcript(['en']).fetch()
                            except Exception:
                                # Fallback if specific language fetching fails or transcripts disabled
                                transcript_list = YouTubeTranscriptApi.list(video_id)
                                transcript_list = next(iter(transcript_list)).fetch()
                                
                            transcript_text = " ".join([t['text'] for t in transcript_list])
                            
                            # Append transcript to context
                            item["content"] = str(item.get("content", "")) + "\n\n=== VIDEO TRANSCRIPT ===\n" + transcript_text
                            
                            # If no summary, make the summary the first 500 chars of the transcript
                            if not item.get("summary"):
                                item["summary"] = transcript_text[:500] + "..."
                    except Exception as e:
                        logger.warning(f"Could not extract YouTube transcript for {link}: {e}")

            # Duplicate checks: same URL or same title
            try:
                if self.storage is not None:
                    if link and getattr(self.storage, "article_exists", None):
                        if self.storage.article_exists(link):
                            logger.debug(f"Skipping duplicate by URL: {link}")
                            if not config.get("include_historical", True):
                                new_items.append(item)
                            return
                            
                    if title and getattr(self.storage, "article_exists_by_title", None):
                        if self.storage.article_exists_by_title(title, source):
                            logger.debug(f"Skipping duplicate by title from same source: {title}")
                            if not config.get("include_historical", True):
                                new_items.append(item)
                            return

                    # Fallback old method if defined, just in case
                    if title and getattr(self.storage, "title_exists", None) and not getattr(self.storage, "article_exists_by_title", None):
                        if self.storage.title_exists(title):
                            logger.debug(f"Skipping duplicate by title (legacy): {title}")
                            if not config.get("include_historical", True):
                                new_items.append(item)
                            return

                    res = self.storage.save_item(item)
                    if not res.get("duplicate", False):
                        new_items.append(item)
                else:
                    # No storage: we cannot determine if new since last run — include
                    new_items.append(item)
            except Exception as e:
                logger.error(f"Error saving or deduping item: {e}")

        # Collect RSS feeds — parallel HTTP requests for speed
        def _fetch_one_rss(f):
            try:
                items = fetch_rss(f, max_items=max_feed)
                if 'news.google.com' in f:
                    import urllib.parse
                    parsed = urllib.parse.urlparse(f)
                    params = urllib.parse.parse_qs(parsed.query)
                    gn_topic = params.get('q', [''])[0]
                    if gn_topic:
                        for item in items:
                            item['auto_pass'] = True
                            item['auto_pass_topic'] = gn_topic
                return items
            except Exception as e:
                logger.error(f"Failed to fetch RSS {f}: {e}")
                return []

        all_rss_entries: List[Dict] = []
        with ThreadPoolExecutor(max_workers=min(15, len(feeds) or 1)) as executor:
            feeds_enabled = config.get('feeds_enabled', {})
            active_feeds = [f for f in feeds if feeds_enabled.get(f, True)] if config.get("enable_rss_feeds", True) else []
            futures = [executor.submit(_fetch_one_rss, f) for f in active_feeds]
            for future in as_completed(futures):
                all_rss_entries.extend(future.result())

        for e in all_rss_entries:
            _process_entry(e)

        # Collect APIs
        if config.get("enable_rss_feeds", True):
            for a in apis:
                if isinstance(a, dict):
                    url = a.get("url")
                    items_path = a.get("items_path")
                else:
                    url = a
                    items_path = None
                if not url:
                    continue
                try:
                    api_items = fetch_json_api(url, items_path=items_path, max_items=config.get("max_items_per_feed", 50))
                except Exception as e:
                    logger.error(f"Failed to fetch API {url}: {e}")
                    api_items = []

                for e in api_items:
                    _process_entry(e)

        # Autonomous Web Search Integration (DuckDuckGo News)
        do_news = config.get("enable_autonomous_search", False)
        do_youtube = config.get("enable_youtube_transcripts", False)
        
        if do_news or do_youtube:
            logger.info("Autonomous Web Search enabled: Searching topics...")
            try:
                from ddgs import DDGS
                with DDGS() as ddgs:
                    topics = config.get("topics", [])
                    for t in topics:
                        t_name = t.get('name', t) if isinstance(t, dict) else t
                        
                        if do_youtube:
                            logger.info(f"Searching YouTube videos for: {t_name}")
                            try:
                                video_results = list(ddgs.videos(f"{t_name} news recent", max_results=5))
                                for vres in video_results:
                                    if 'youtube.com' in vres.get("content", ""):
                                        from datetime import datetime
                                        video_entry = {
                                            "title": vres.get("title", ""),
                                            "link": vres.get("content", ""), # DDGS puts the URL in 'content' for videos
                                            "published": vres.get("published", datetime.utcnow().isoformat()),
                                            "summary": vres.get("description", ""),
                                            "source": vres.get("uploader", "YouTube"),
                                            "fetched_at": datetime.utcnow().isoformat()
                                        }
                                        _process_entry(video_entry)
                            except Exception as ve:
                                logger.warning(f"DuckDuckGo video search failed for {t_name}: {ve}")
                                
                        if do_news:
                            search_query = f"{t_name} news"
                            logger.info(f"Searching web for: {search_query}")
                            try:
                                # Get top 5 news articles per topic
                                results = list(ddgs.news(search_query, max_results=5))
                                for res in results:
                                    from datetime import datetime
                                    # DDG News returns: title, url, source, date, body
                                    entry = {
                                        "title": res.get("title", ""),
                                        "link": res.get("url", ""),
                                        "published": res.get("date", datetime.utcnow().isoformat()),
                                        "summary": res.get("body", ""),
                                        "source": res.get("source", "DuckDuckGo Search"),
                                        "fetched_at": datetime.utcnow().isoformat()
                                    }
                                    _process_entry(entry)
                            except Exception as pe:
                                logger.warning(f"DuckDuckGo news search failed for {t_name}: {pe}")

                        import time
                        time.sleep(2)  # Prevent DDG rate limit
            except Exception as e:
                logger.error(f"DuckDuckGo search failed: {e}")

        logger.info(f"Collector: inserted {len(new_items)} new items")
        return new_items

