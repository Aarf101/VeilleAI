#!/usr/bin/env python3
from pathlib import Path
import os

# Set working directory to script location
os.chdir(Path(__file__).parent)

print(f"Working directory: {os.getcwd()}")

def load_env_file():
    env_path = Path('.env')
    if not env_path.exists():
        print("WARNING: .env file not found!")
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()
    print("Loaded .env file successfully")

load_env_file()  # call this FIRST before anything else

import sys
try:
    import sgmllib
except ImportError:
    try:
        import sgmllib3k as sgmllib
        sys.modules['sgmllib'] = sgmllib
    except ImportError:
        pass

import io

sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer, 
    encoding='utf-8', 
    errors='replace'
)
sys.stderr = io.TextIOWrapper(
    sys.stderr.buffer,
    encoding='utf-8',
    errors='replace'
)

def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(str(text).encode('ascii', 'replace').decode('ascii'))

sys.path.insert(0, str(Path(__file__).parent))

from watcher.config import load_config
from watcher.storage.store import Storage
from watcher.agents.collector import CollectorAgent
from watcher.agents.filter import SmartFilter
from watcher.agents.synthesizer import generate_report
from watcher.agents.llm_api_adapter import APILLMAdapter

import sqlite3

def get_recent_articles_from_db(config, days=7):
    db_path = config.get(
        'sqlite_path',
        config.get('database', 'watcher.db')
    )
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("""
            SELECT title, url, 
                   published, summary, source
            FROM items 
            WHERE published >= date('now', '-7 days')
            OR published >= datetime('now', '-7 days')
            OR published IS NULL
            OR published = ''
            ORDER BY id DESC
            LIMIT 200
        """)
        rows = c.fetchall()
        conn.close()
        articles = []
        for row in rows:
            articles.append({
                'title':     row[0] or '',
                'url':       row[1] or '',
                'link':      row[1] or '',
                'published': row[2] or '',
                'summary':   row[3] or '',
                'source':    row[4] or '',
            })
        safe_print(f"DB: {len(articles)} recent articles")
        return articles
    except Exception as e:
        safe_print(f"DB error: {e}")
        return []

def apply_recency_boost(articles, config):
    if not config.get('recency_boost', False):
        return articles
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    for art in articles:
        bonus = 0.0
        pub = art.get('published', '') or ''
        try:
            # Try multiple common formats
            for fmt in ('%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d'):
                try:
                    # Clean the string for strptime (some RSS add extra stuff)
                    dt = datetime.strptime(pub[:25].strip(), fmt)
                    if dt.tzinfo:
                        dt = dt.replace(tzinfo=None)
                    age_days = (now - dt).days
                    if age_days == 0:
                        bonus = 0.15
                    elif age_days == 1:
                        bonus = 0.10
                    elif age_days > 7:
                        bonus = -0.05
                    break
                except:
                    continue
        except:
            pass
        art['recency_bonus'] = bonus
        # Weighting relevance_score if it exists
        current_score = art.get('relevance_score', 0.5)
        art['relevance_score'] = round(min(1.0, max(0.0, current_score + bonus)), 2)
    return articles

def collect_all_feeds(config):
    db_path = config.get(
        'sqlite_path',
        config.get('database', 'watcher.db')
    )
    storage = Storage(db_path)
    
    pipeline_mode = os.environ.get("PIPELINE_MODE", "Keep existing")
    if pipeline_mode == "Fresh start":
        safe_print("Mode 'Fresh start': clearing database to fetch all articles...")
        try:
            cur = storage.conn.cursor()
            cur.execute("DELETE FROM items")
            storage.conn.commit()
        except Exception as e:
            safe_print(f"Error clearing db: {e}")
    elif pipeline_mode == "Clear old >7 days":
        safe_print("Mode 'Clear old >7 days': purging records older than 7 days...")
        try:
            cur = storage.conn.cursor()
            cur.execute("DELETE FROM items WHERE fetched_at < date('now', '-7 days')")
            storage.conn.commit()
        except:
            pass

    collector = CollectorAgent(
        storage=storage,
        config=config
    )
    return collector.collect_new()

FINANCE_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://coindesk.com/arc/outboundfeeds/rss/",
    "https://decrypt.co/feed",
    "https://feeds.feedburner.com/entrepreneur/latest",
]

def ensure_feeds_for_topics(config):
    topics = config.get('topics', [])
    feeds  = config.get('feeds', [])
    
    finance_keywords = [
        'crypto', 'bitcoin', 'fintech', 
        'stock', 'venture', 'startup', 'funding'
    ]
    
    needs_finance = any(
        any(kw in t.lower() for kw in finance_keywords)
        for t in topics
    )
    
    if needs_finance:
        for feed in FINANCE_FEEDS:
            if feed not in feeds:
                feeds.append(feed)
        config['feeds'] = feeds
    
    return config

def run_pipeline(config):
    config = ensure_feeds_for_topics(config)
    topics    = config.get('topics', [])
    threshold = min(config.get('relevance_threshold', 0.25), 0.30)
    
    # Step 1: Collect articles
    safe_print("Step 1: Collecting articles...")
    new_articles = collect_all_feeds(config)
    safe_print(f"New: {len(new_articles)} articles")

    # Also get recent from DB
    db_articles = get_recent_articles_from_db(config)
    safe_print(f"From DB: {len(db_articles)} articles")

    # Combine both
    all_articles = new_articles + db_articles
    # Remove duplicates by URL
    seen_urls = set()
    articles = []
    for art in all_articles:
        url = art.get('url','') or art.get('link','')
        if url and url not in seen_urls:
            seen_urls.add(url)
            articles.append(art)
        elif not url:
            articles.append(art)

    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=30)
    
    recent_articles = []
    for art in articles:
        try:
            pub = art.get('published','')
            if pub:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(pub)
                dt = dt.replace(tzinfo=None)
                if dt >= cutoff:
                    recent_articles.append(art)
            else:
                recent_articles.append(art)
        except:
            recent_articles.append(art)
            
    articles = recent_articles
    safe_print(f"Recent articles (30 days): {len(articles)}")
    safe_print(f"Total unique: {len(articles)} articles")
    
    if len(articles) == 0:
        safe_print("ERROR: No articles collected!")
        safe_print("Check your RSS feeds in Data Sources")
        return None
        
    def is_google_news(url):
        if not url: return False
        return 'news.google.com' in str(url)

    for article in articles:
        if is_google_news(article.get('feed_url','')):
            article['skip_filter'] = True
    
    # Step 2: Smart filter per topic
    safe_print("Step 2: Filtering by topic...")
    smart_filter = SmartFilter(topics, threshold, config)
    filtered_by_topic = smart_filter.filter_all(articles)
    
    # Apply recency boost to all matched articles
    for topic in filtered_by_topic:
        filtered_by_topic[topic] = apply_recency_boost(filtered_by_topic[topic], config)

    # Cross-topic deduplication
    seen_urls = {} # url -> best_article_object
    for topic, arts in filtered_by_topic.items():
        for art in arts:
            url = art.get('url', '') or art.get('link', '')
            if not url: continue
            
            if url in seen_urls:
                existing = seen_urls[url]
                # If current match is better, swap
                if art.get('relevance_score', 0) > existing.get('relevance_score', 0):
                    # Add old topic to also_relevant
                    art['also_relevant_for'] = art.get('also_relevant_for', [])
                    if existing.get('matched_topic') not in art['also_relevant_for']:
                        art['also_relevant_for'].append(existing.get('matched_topic'))
                    seen_urls[url] = art
                else:
                    # Current is worse, just add current topic to existing's also_relevant
                    existing['also_relevant_for'] = existing.get('also_relevant_for', [])
                    if topic not in existing['also_relevant_for']:
                        existing['also_relevant_for'].append(topic)
            else:
                seen_urls[url] = art

    # Rebuild filtered_by_topic using only the "best" versions
    new_filtered = {topic: [] for topic in topics}
    for url, art in seen_urls.items():
        best_topic = art.get('matched_topic')
        if best_topic in new_filtered:
            new_filtered[best_topic].append(art)
    
    filtered_by_topic = new_filtered
    
    # Log results
    safe_print(f"Step 2 results:")
    for topic, arts in filtered_by_topic.items():
        safe_print(f"  {topic}: {len(arts)} articles ready for LLM")
    safe_print(f"Total for LLM: {sum(len(v) for v in filtered_by_topic.values())}")
    
    # Init LLM client
    def get_config_value(config, *keys, default=''):
        for key in keys:
            if key in config and config[key]:
                return config[key]
        return default

    try:
        api_provider = get_config_value(
            config, 
            'provider', 'api_provider',
            default='groq'
        )
        api_model = get_config_value(
            config,
            'model', 'api_model', 
            default='llama-3.3-70b-versatile'
        )
        llm_client = APILLMAdapter(provider=api_provider, model=api_model)
    except Exception as e:
        safe_print(f"ERROR initializing LLM client: {e}")
        return None

    # Step 3: Generate report per topic
    safe_print("Step 3: Generating report...")
    report = generate_report(
        filtered_by_topic, config, llm_client
    )
    
    # Step 4: Save report
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"reports/intelligence_report_{timestamp}.md"
    
    os.makedirs("reports", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    safe_print(f"Report saved: {filename}")
    
    # Diagnostic output
    safe_print("\n" + "="*50)
    safe_print("PIPELINE SUMMARY")
    safe_print("="*50)
    safe_print(f"Articles collected: {len(articles)}")
    for topic, arts in filtered_by_topic.items():
        status = "[OK]" if len(arts) > 0 else "[--]"
        safe_print(f"{status} {topic}: {len(arts)} articles")
    safe_print(f"Report: {filename}")
    safe_print("="*50)
    
    return filename

if __name__ == "__main__":
    cfg = load_config() or {}
    run_pipeline(cfg)
