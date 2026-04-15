import re
from watcher.collectors.rss import _fetch_summary_from_url, fetch_feed_with_timeout, datetime, logger
import feedparser

def _parse_rss_xml(content):
    pass # Deprecated, remove later

def fetch_rss(feed_url: str, max_items: int = 10) -> list[dict]:
    content = fetch_feed_with_timeout(feed_url, timeout=10)
    if not content:
        return []
    
    try:
        parsed = feedparser.parse(content)
    except Exception as e:
        logger.warning(f"feedparser parse error: {e}")
        return []
    
    source = parsed.feed.get('title', feed_url)
    items = []
    for entry in parsed.entries[:max_items]:
        link = entry.get('link', '')
        summary = entry.get('summary', '')
        content_val = summary
        if 'content' in entry and len(entry.content) > 0:
            content_val = entry.content[0].get('value', summary)
            
        published = entry.get('published', '') or entry.get('updated', '')
        
        clean_summary = re.sub(r'<[^>]+>', '', summary).strip() if summary else ''
        if len(clean_summary) < 50 and link:
            new_summary = _fetch_summary_from_url(link, timeout=5)
            if new_summary:
                summary = new_summary
            if not content_val:
                content_val = summary
        
        items.append({
            'title': entry.get('title', ''),
            'link': link,
            'published': published,
            'summary': summary,
            'content': content_val,
            'source': source,
            'feed_url': feed_url,
            'fetched_at': datetime.utcnow().isoformat() + 'Z',
        })
    
    return items
