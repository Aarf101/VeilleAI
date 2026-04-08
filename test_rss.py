from watcher.collectors.rss import fetch_rss
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

test_feed = "https://techcrunch.com/feed/"
try:
    print(f"Fetching: {test_feed}")
    items = fetch_rss(test_feed, max_items=5)
    print(f"Fetched {len(items)} items")
    for item in items:
        print(f"Title: {item.get('title')}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
