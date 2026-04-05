from pathlib import Path
import yaml

# Always points to the real config.yaml
# regardless of where the script is launched from
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

def load_config(path=None):
    p = Path(path) if path else CONFIG_PATH
    if not p.exists():
        p = Path("config.yaml").resolve()
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
        # After loading, normalize topics
        if 'topics' in config:
            normalized = []
            for t in config['topics']:
                if isinstance(t, dict):
                    normalized.append(t)
                else:
                    normalized.append({'name': t, 'description': t})
            config['topics'] = normalized
        
        print(f"[config] Loaded: {p}")
        print(f"[config] Feeds: {len(config.get('feeds',[]))}")
        print(f"[config] Topics: {config.get('topics',[])}")
        return config


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
