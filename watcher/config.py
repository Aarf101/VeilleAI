from pathlib import Path
import yaml


def load_config(path: str | Path = "config.yaml") -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def sample_default() -> dict:
    return {
        "database": "watcher.db",
        "feeds": [
            "https://news.ycombinator.com/rss",
        ],
        "apis": [
            # Example: {"url": "https://api.example.com/news", "items_path": "data.items"}
        ],
        "max_items_per_feed": 10,
    }
