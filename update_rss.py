import re

with open("watcher/collectors/rss.py", "r") as f:
    text = f.read()

# We need to replace the _parse_rss_xml and fetch_rss functions
def_start = text.find("def _parse_rss_xml(content):")
if def_start != -1:
    # Find the end of fetch_rss
    fetch_rss_start = text.find("def fetch_rss", def_start)
    next_def = text.find("def ", fetch_rss_start + 10)
    if next_def == -1:
        end_idx = len(text)
    else:
        end_idx = next_def
        
    new_code = """import feedparser

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
"""
    # Don't forget to import feedparser at the top
    if "import feedparser" not in text[:def_start]:
        import_block = "import feedparser\n"
    else:
        import_block = ""
        
    final_text = import_block + text[:def_start] + new_code + text[end_idx:]
    with open("watcher/collectors/rss.py", "w") as f:
        f.write(final_text)
    print("Successfully patched watcher/collectors/rss.py")
else:
    print("Could not find _parse_rss_xml in rss.py")
