"""Collector Agent - collect raw items from configured sources.

Responsibilities implemented here:
- Fetch RSS feeds and JSON APIs configured in `config.yaml`
- Extract required fields (title, published, source, url, summary/content)
- Skip obvious duplicates (same URL or same title) using storage
- Persist new items with `Storage.save_item` and return only newly inserted items
"""
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class CollectorAgent:
    """Collector that gathers raw items and persists deduplicated ones.

    If a `storage` instance is provided it will be used to detect duplicates and
    persist items. The method `collect_new()` returns a list of newly inserted
    items (as stored) which can then be passed to a filtering agent.
    """

    def __init__(self, storage=None):
        self.storage = storage

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

        config = load_config() or {}
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

            # Duplicate checks: same URL or same title
            try:
                if self.storage is not None:
                    if link:
                        # storage.save_item will catch url duplicates, try quick check
                        pass
                    if title and getattr(self.storage, "title_exists", None):
                        if self.storage.title_exists(title):
                            logger.debug(f"Skipping duplicate by title: {title}")
                            return

                    res = self.storage.save_item(item)
                    if not res.get("duplicate", False):
                        new_items.append(item)
                else:
                    # No storage: we cannot determine if new since last run — include
                    new_items.append(item)
            except Exception as e:
                logger.error(f"Error saving or deduping item: {e}")

        # Collect RSS feeds
        for f in feeds:
            try:
                feed_items = fetch_rss(f, max_items=max_feed)
            except Exception as e:
                logger.error(f"Failed to fetch RSS {f}: {e}")
                feed_items = []

            for e in feed_items:
                _process_entry(e)

        # Collect APIs
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

        logger.info(f"Collector: inserted {len(new_items)} new items")
        return new_items

