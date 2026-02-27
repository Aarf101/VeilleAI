"""Demo runner for collectors and storage (Agent Collecteur smoke-test).

Usage: python demo/run_collectors.py

This script is defensive: if `feedparser` or `requests` are missing it prints
instructions instead of failing loudly.
"""
from pathlib import Path
import sys
# Ensure project root is on PYTHONPATH so `import watcher` works when running
# this script directly: `python3 demo/run_collectors.py`
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from watcher import config
from watcher.storage.store import Storage


def main():
    cfg = config.load_config() or config.sample_default()
    db_path = cfg.get("database", "watcher.db")
    st = Storage(db_path)

    feeds = cfg.get("feeds", [])
    apis = cfg.get("apis", [])
    max_items = cfg.get("max_items_per_feed", 10)

    total_new = 0
    for f in feeds:
        print(f"Collecting RSS feed: {f}")
        try:
            from watcher.collectors.rss import fetch_rss

            items = fetch_rss(f, max_items=max_items)
        except ImportError as e:
            print("Missing RSS dependency:", e)
            print("Install dependencies with: pip install feedparser requests")
            sys.exit(1)
        except Exception as e:
            print("RSS fetch failed:", e)
            items = []

        for it in items:
            res = st.save_item(it)
            if not res["duplicate"]:
                total_new += 1

    for a in apis:
        url = a.get("url") if isinstance(a, dict) else a
        items_path = a.get("items_path") if isinstance(a, dict) else None
        print(f"Collecting API: {url}")
        try:
            from watcher.collectors.api import fetch_json_api

            items = fetch_json_api(url, items_path=items_path, max_items=cfg.get("max_items_per_feed", 20))
        except ImportError as e:
            print("Missing API dependency:", e)
            print("Install dependencies with: pip install requests")
            sys.exit(1)
        except Exception as e:
            print("API fetch failed:", e)
            items = []

        for it in items:
            res = st.save_item(it)
            if not res["duplicate"]:
                total_new += 1

    print(f"Demo finished — new items inserted: {total_new}")
    print("Recent items:")
    for r in st.list_items(10):
        print(r)


if __name__ == "__main__":
    main()
