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

def _parse_rss_xml(content):
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        logger.warning(f"XML parse error: {e}")
        return [], ""
    
    ns = {'atom': 'http://www.w3.org/2005/Atom',
          'media': 'http://search.yahoo.com/mrss/'}
    
    # Detect feed type
    tag = root.tag.lower()
    entries = []
    feed_title = ""
    
    if 'rss' in tag or root.find('channel') is not None:
        # RSS format
        channel = root.find('channel')
        if channel is None:
            return [], ""
        feed_title = (channel.findtext('title') or '').strip()
        for item in channel.findall('item'):
            entries.append({
                'title': (item.findtext('title') or '').strip(),
                'link': (item.findtext('link') or '').strip(),
                'published': (item.findtext('pubDate') or item.findtext('dc:date') or '').strip(),
                'summary': (item.findtext('description') or '').strip(),
                'content': (item.findtext('content:encoded') or item.findtext('description') or '').strip(),
            })
    elif 'feed' in tag:
        # Atom format
        feed_title_el = root.find('atom:title', ns) or root.find('title')
        feed_title = (feed_title_el.text if feed_title_el is not None else '').strip()
        for entry in (root.findall('atom:entry', ns) or root.findall('entry')):
            link_el = entry.find('atom:link', ns) or entry.find('link')
            link = ''
            if link_el is not None:
                link = link_el.get('href', '') or link_el.text or ''
            title_el = entry.find('atom:title', ns) or entry.find('title')
            summary_el = entry.find('atom:summary', ns) or entry.find('summary')
            content_el = entry.find('atom:content', ns) or entry.find('content')
            published_el = entry.find('atom:published', ns) or entry.find('published') or entry.find('updated')
            entries.append({
                'title': (title_el.text if title_el is not None else '').strip(),
                'link': link.strip(),
                'published': (published_el.text if published_el is not None else '').strip(),
                'summary': (summary_el.text if summary_el is not None else '').strip(),
                'content': (content_el.text if content_el is not None else '').strip(),
            })
    
    return entries, feed_title

def fetch_rss(feed_url: str, max_items: int = 10) -> list[dict]:
    content = fetch_feed_with_timeout(feed_url, timeout=10)
    if not content:
        return []
    
    entries, feed_title = _parse_rss_xml(content)
    source = feed_title or feed_url
    
    items = []
    for entry in entries[:max_items]:
        link = entry.get('link', '')
        summary = entry.get('summary', '')
        content = entry.get('content', '') or summary
        
        # If summary too short, try fetching from real page
        clean_summary = re.sub(r'<[^>]+>', '', summary).strip()
        if len(clean_summary) < 50 and link:
            new_summary = _fetch_summary_from_url(link, timeout=5)
            if new_summary:
                summary = new_summary
        
        items.append({
            'title': entry.get('title', ''),
            'link': link,
            'published': entry.get('published', ''),
            'summary': summary,
            'content': content,
            'source': source,
            'feed_url': feed_url,
            'fetched_at': datetime.utcnow().isoformat() + 'Z',
        })
    
    return items
