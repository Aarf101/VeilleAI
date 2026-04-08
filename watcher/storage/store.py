"""Simple SQLite storage with deduplication hooks."""
import sqlite3
from pathlib import Path
from typing import Dict, Optional
import hashlib
from datetime import datetime
from typing import Any

from watcher import config as _config

_VECTOR_STORE = None
_EMB_PROVIDER = None
_CHROMA_DIR = None
try:
    cfg = _config.load_config()
    _CHROMA_DIR = (cfg.get("chroma_path") or cfg.get("chroma_persist_dir")) if cfg else None
except Exception:
    _CHROMA_DIR = None
try:
    from watcher.storage.vector_store import VectorStore
    from watcher.nlp.embeddings import EmbeddingProvider

    _VECTOR_STORE = VectorStore(persist_directory=_CHROMA_DIR)
    _EMB_PROVIDER = EmbeddingProvider()
except Exception:
    # If dependencies missing, leave as None and skip persistence
    _VECTOR_STORE = None
    _EMB_PROVIDER = None


class Storage:
    def __init__(self, db_path: str | Path = "watcher.db"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self._init_db()

    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE,
            title TEXT,
            published TEXT,
            summary TEXT,
            content TEXT,
            source TEXT,
            fetched_at TEXT,
            content_hash TEXT
        )
        """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_items_hash ON items(content_hash)"
        )
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_url ON items(url)"
        )
        self.conn.commit()

    def article_exists(self, url: str) -> bool:
        if not url: return False
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM items WHERE url = ?", (url,))
        return cur.fetchone()[0] > 0

    def article_exists_by_title(self, title: str, source: str) -> bool:
        if not title: return False
        cur = self.conn.cursor()
        if source:
            cur.execute("SELECT COUNT(*) FROM items WHERE title = ? AND source = ?", (title, source))
        else:
            cur.execute("SELECT COUNT(*) FROM items WHERE title = ?", (title,))
        return cur.fetchone()[0] > 0

    def _hash_item(self, item: Dict) -> str:
        s = (
            (item.get("title") or "") + "\n" + (item.get("summary") or "") + "\n" + (item.get("content") or "")
        )
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    def save_item(self, item: Dict) -> Dict[str, Optional[int]]:
        """Save item if not duplicate. Return dict {'inserted_id': int|None, 'duplicate': bool}.

        Dedup by URL uniqueness and by content_hash.
        """
        cur = self.conn.cursor()
        url = item.get("link") or item.get("url") or None
        ch = self._hash_item(item)

        # check by url
        if url:
            cur.execute("SELECT id FROM items WHERE url = ?", (url,))
            row = cur.fetchone()
            if row:
                return {"inserted_id": row[0], "duplicate": True}

        # check by content hash
        cur.execute("SELECT id FROM items WHERE content_hash = ?", (ch,))
        row = cur.fetchone()
        if row:
            return {"inserted_id": row[0], "duplicate": True}

        cur.execute(
            """
        INSERT INTO items (url, title, published, summary, content, source, fetched_at, content_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                url,
                item.get("title"),
                item.get("published"),
                item.get("summary"),
                item.get("content"),
                item.get("source"),
                item.get("fetched_at", datetime.utcnow().isoformat() + "Z"),
                ch,
            ),
        )
        self.conn.commit()
        inserted_id = cur.lastrowid

        # Persist embedding in vector store (if available)
        try:
            if _VECTOR_STORE is not None and _EMB_PROVIDER is not None:
                text = (item.get("content") or item.get("summary") or item.get("title") or "").strip()
                if text:
                    emb = _EMB_PROVIDER.embed([text])[0].tolist()
                    # use DB id as vector id
                    _VECTOR_STORE.add(ids=[str(inserted_id)], embeddings=[emb], metadatas=[{"url": url, "title": item.get("title")}])
        except Exception:
            # don't fail saving if vector persistence fails
            pass

        return {"inserted_id": inserted_id, "duplicate": False}

    def list_items(self, limit: int = 100):
        cur = self.conn.cursor()
        cur.execute("SELECT id, url, title, published, source FROM items ORDER BY id DESC LIMIT ?", (limit,))
        return cur.fetchall()

    def get_item_by_id(self, item_id: int) -> dict | None:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, url, title, published, summary, content, source, fetched_at, content_hash FROM items WHERE id = ?",
            (item_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        keys = ["id", "url", "title", "published", "summary", "content", "source", "fetched_at", "content_hash"]
        return dict(zip(keys, row))

    def get_recent_items_full(self, limit: int = 100) -> list:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, url, title, published, summary, content, source, fetched_at, content_hash FROM items ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        keys = ["id", "url", "title", "published", "summary", "content", "source", "fetched_at", "content_hash"]
        return [dict(zip(keys, r)) for r in rows]

    def title_exists(self, title: str) -> bool:
        """Return True if an item with the exact title already exists in DB."""
        if not title:
            return False
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM items WHERE title = ? LIMIT 1", (title,))
        return cur.fetchone() is not None

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass
