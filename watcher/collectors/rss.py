"""Simple RSS collector - uses feedparser if available."""
from typing import List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def _fetch_article_content(url: str, timeout: int = 3) -> str:
    """Fetch full article content from URL using web scraping.
    
    Args:
        url: Article URL to scrape
        timeout: Request timeout in seconds
        
    Returns:
        Extracted article text or empty string if failed
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Remove script, style, nav, footer elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Try common article selectors
        article = None
        selectors = [
            'article',
            '[class*="article-content"]',
            '[class*="post-content"]',
            '[class*="entry-content"]',
            'main',
            '.content'
        ]
        
        for selector in selectors:
            article = soup.select_one(selector)
            if article:
                break
        
        if article:
            # Get all paragraphs
            paragraphs = article.find_all('p')
            text = '\n\n'.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
            return text[:5000]  # Limit to 5000 chars
        
        # Fallback: get all paragraphs
        paragraphs = soup.find_all('p')
        text = '\n\n'.join(p.get_text().strip() for p in paragraphs[:10] if p.get_text().strip())
        return text[:5000]
        
    except Exception as e:
        logger.debug(f"Failed to fetch article content from {url}: {e}")
        return ""


def fetch_rss(feed_url: str, max_items: int = 10) -> List[dict]:
    try:
        import feedparser
    except Exception as e:
        raise ImportError(
            "feedparser is required for RSS collection. Install with: pip install feedparser"
        ) from e

    parsed = feedparser.parse(feed_url)
    items = []
    source = parsed.feed.get("title") if getattr(parsed, "feed", None) else feed_url
    for entry in parsed.entries[:max_items]:
        summary = entry.get("summary", "")
        content = _extract_content(entry)
        link = entry.get("link", "")
        
        # If content is too short, try fetching full article
        if len(content) < 200 and link:
            logger.debug(f"Fetching full content for: {entry.get('title', 'Unknown')}")
            full_content = _fetch_article_content(link)
            if len(full_content) > len(content):
                content = full_content
        
        items.append(
            {
                "title": entry.get("title", ""),
                "link": link,
                "published": entry.get("published", entry.get("updated", None)),
                "summary": summary,
                "content": content,
                "source": source,
                "fetched_at": datetime.utcnow().isoformat() + "Z",
            }
        )
    return items


def _extract_content(entry) -> str:
    # feedparser may expose content[] for full text
    if "content" in entry and entry.content:
        try:
            return entry.content[0].value
        except Exception:
            return str(entry.get("summary", ""))
    return str(entry.get("summary", ""))
