"""Generic JSON API collector.

Expect API entries as a list located under a dotted `items_path` (e.g. "data.items").
"""
from typing import List, Any
from datetime import datetime


def fetch_json_api(url: str, items_path: str | None = None, max_items: int = 50) -> List[dict]:
    try:
        import requests
    except Exception as e:
        raise ImportError(
            "requests is required for API collection. Install with: pip install requests"
        ) from e

    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    items = _extract_items_from_json(data, items_path)
    results = []
    for entry in items[:max_items]:
        results.append(
            {
                "title": _get_field(entry, ["title", "headline", "name"]),
                "link": _get_field(entry, ["url", "link"]),
                "published": _get_field(entry, ["published", "date", "created_at"]),
                "summary": _get_field(entry, ["summary", "description", "excerpt"]),
                "content": _get_field(entry, ["content", "body", "text"]),
                "source": url,
                "fetched_at": datetime.utcnow().isoformat() + "Z",
            }
        )
    return results


def _extract_items_from_json(data: Any, items_path: str | None) -> List[Any]:
    if not items_path:
        # try common keys
        for key in ("items", "data", "results", "articles"):
            if isinstance(data, dict) and key in data:
                return data[key]
        if isinstance(data, list):
            return data
        return []
    # follow dotted path
    node = data
    for part in items_path.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return []
    return node if isinstance(node, list) else []


def _get_field(obj: Any, candidates: list) -> str:
    if not obj:
        return ""
    if isinstance(obj, dict):
        for k in candidates:
            if k in obj:
                return obj[k] or ""
    # fallback to string
    return str(obj)
