import feedparser
import requests
import xml.etree.ElementTree as ET
import socket
from datetime import datetime
import logging
import re

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

def _fetch_summary_from_url(url: str, timeout: int = 5) -> str:
    """Fetch real article URL and extract first 300 words if summary is empty."""
    try:
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script, style, nav, footer, ads, etc.
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
            element.decompose()
            
        # Extract text and clean up whitespaces
        text = soup.get_text(separator=' ', strip=True)
        words = text.split()
        return ' '.join(words[:300])
        
    except Exception as e:
        logger.debug(f"Failed to fetch summary from webpage {url}: {e}")
        return ""

def fetch_feed_with_timeout(url, timeout=10):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)'}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.warning(f"SKIPPED feed {url}: {e}")
        return None

import feedparser

def fetch_rss(feed_url: str, max_items: int = 10) -> list[dict]:
    content = fetch_feed_with_timeout(feed_url, timeout=10)
    if not content:
        return []
    
    try:
        parsed = feedparser.parse(content)
    except Exception as e:
        logger.warning(f"feedparser parse error for {feed_url}: {e}")
        return []
        
    source = parsed.feed.get('title', feed_url)
    
    items = []
    for entry in parsed.entries[:max_items]:
        link = entry.get('link', '')
        
        # Get safest summary
        summary = entry.get('summary', '')
        content_val = summary
        if 'content' in entry and len(entry.content) > 0:
            content_val = entry.content[0].get('value', summary)
            
        published = entry.get('published', '') or entry.get('updated', '')
        
        # If summary too short, try fetching from real page
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
