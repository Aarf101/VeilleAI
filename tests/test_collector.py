import os
import pytest
from unittest.mock import patch
from watcher.storage.store import Storage
from watcher.agents.collector import CollectorAgent


@pytest.fixture
def mock_no_vector_store(monkeypatch):
    """Disable vector store to avoid slow embeddings during tests."""
    monkeypatch.setenv("CHROMADB_DISABLED", "1")
    import watcher.storage.store as store_module
    store_module._VECTOR_STORE = None
    store_module._EMB_PROVIDER = None


def test_collector_inserts_only_unique_items(tmp_path, monkeypatch, mock_no_vector_store):
    """Test that collector deduplicates items by title and URL."""
    # Prepare mocked feed and api items
    rss_items = [
        {"title": "A", "link": "http://a", "published": "2026-02-10", "summary": "s1", "content": "c1", "source": "feed"},
        {"title": "B", "link": "http://b", "published": "2026-02-10", "summary": "s2", "content": "c2", "source": "feed"},
    ]

    api_items = [
        # same title as RSS B -> should be considered duplicate by title
        {"title": "B", "url": "http://b2", "published": "2026-02-10", "summary": "s2b", "content": "c2b", "source": "api"},
        {"title": "C", "url": "http://c", "published": "2026-02-10", "summary": "s3", "content": "c3", "source": "api"},
    ]

    # Mock config to return our test feeds
    test_config = {
        "database": str(tmp_path / "test.db"),
        "feeds": ["http://test-feed"],
        "apis": [{"url": "http://test-api", "items_path": None}],
        "max_items_per_feed": 10,
    }

    # Monkeypatch to use test config and mocked fetch functions
    monkeypatch.setattr("watcher.config.load_config", lambda: test_config)
    monkeypatch.setattr("watcher.collectors.rss.fetch_rss", lambda url, max_items=10: rss_items)
    monkeypatch.setattr("watcher.collectors.api.fetch_json_api", lambda url, items_path=None, max_items=50: api_items)

    dbfile = tmp_path / "test_watch.db"
    st = Storage(str(dbfile))

    agent = CollectorAgent(storage=st)
    new = agent.collect_new()

    # Expect 3 unique inserts: A, B, C (B from API skipped due to same title)
    assert len(new) == 3, f"Expected 3 new items but got {len(new)}: {[i.get('title') for i in new]}"

    rows = st.list_items(10)
    assert len(rows) == 3, f"Expected 3 rows in DB but got {len(rows)}"

    titles = {r[2] for r in rows}
    assert titles == {"A", "B", "C"}, f"Expected titles A,B,C but got {titles}"

    st.close()
