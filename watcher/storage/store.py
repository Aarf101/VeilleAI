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
        # Enable multi-threaded access
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        import threading
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self.lock:
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
                content_hash TEXT,
                topic TEXT
            )
            """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_items_hash ON items(content_hash)"
            )
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_url ON items(url)"
            )
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    type TEXT
                )
                '''
            )
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS item_entities (
                    item_id INTEGER,
                    entity_id INTEGER,
                    mention_time TEXT,
                    FOREIGN KEY(item_id) REFERENCES items(id),
                    FOREIGN KEY(entity_id) REFERENCES entities(id),
                    UNIQUE(item_id, entity_id)
                )
                '''
            )
            self.conn.commit()

    def article_exists(self, url: str) -> bool:
        if not url: return False
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM items WHERE url = ?", (url,))
            return cur.fetchone()[0] > 0

    def article_exists_by_title(self, title: str, source: str) -> bool:
        if not title: return False
        with self.lock:
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
        with self.lock:
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
            INSERT INTO items (url, title, published, summary, content, source, fetched_at, content_hash, topic)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    item.get("matched_topic")
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

    # -------------------- Entity helpers --------------------
    def save_entities_for_item(self, item_id: int, entities: list, mention_time: str = None):
        """Persist extracted entities and link them to the given item_id.

        entities: list of dicts with keys 'name' and optional 'type'
        mention_time: ISO timestamp string (defaults to now)
        """
        import datetime
        with self.lock:
            cur = self.conn.cursor()
            if mention_time is None:
                mention_time = datetime.datetime.utcnow().isoformat() + "Z"

            for ent in entities:
                name = (ent.get('name') or ent.get('entity') or '').strip()
                if not name:
                    continue
                etype = ent.get('type') or ent.get('category') or 'Unknown'
                # normalize
                name_norm = name.title()
                try:
                    cur.execute("INSERT OR IGNORE INTO entities (name, type) VALUES (?, ?)", (name_norm, etype))
                    cur.execute("SELECT id FROM entities WHERE name = ?", (name_norm,))
                    row = cur.fetchone()
                    if not row:
                        continue
                    ent_id = row[0]
                    cur.execute(
                        "INSERT OR IGNORE INTO item_entities (item_id, entity_id, mention_time) VALUES (?, ?, ?)",
                        (item_id, ent_id, mention_time),
                    )
                except Exception:
                    # swallow individual insert errors to avoid failing whole pipeline
                    continue
            self.conn.commit()

    def wipe_all(self):
        """Clear both SQLite items and Vector Store entries."""
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM items")
            self.conn.commit()
        if _VECTOR_STORE:
            _VECTOR_STORE.reset()

    def get_entity_counts(self, since_iso: str, until_iso: str = None) -> list:
        """Return list of (entity_name, count) for mentions between since_iso and until_iso (ISO strings)."""
        with self.lock:
            cur = self.conn.cursor()
            if until_iso:
                cur.execute(
                    "SELECT e.name, COUNT(*) as cnt FROM item_entities ie JOIN entities e ON ie.entity_id = e.id WHERE ie.mention_time BETWEEN ? AND ? GROUP BY e.name ORDER BY cnt DESC",
                    (since_iso, until_iso),
                )
            else:
                cur.execute(
                    "SELECT e.name, COUNT(*) as cnt FROM item_entities ie JOIN entities e ON ie.entity_id = e.id WHERE ie.mention_time >= ? GROUP BY e.name ORDER BY cnt DESC",
                    (since_iso,),
                )
            return cur.fetchall()

    def get_entity_velocity(self, entity_name: str, window_days: int = 7) -> dict:
        """Compute velocity for an entity comparing the latest `window_days` to the previous same-length window.

        Returns dict: {"entity": name, "current": int, "previous": int, "percent_change": float}
        """
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        end_current = now
        start_current = now - timedelta(days=window_days)
        start_prev = start_current - timedelta(days=window_days)
        end_prev = start_current

        with self.lock:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM item_entities ie JOIN entities e ON ie.entity_id = e.id WHERE e.name = ? AND ie.mention_time BETWEEN ? AND ?",
                (entity_name, start_current.isoformat(), end_current.isoformat()),
            )
            current = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM item_entities ie JOIN entities e ON ie.entity_id = e.id WHERE e.name = ? AND ie.mention_time BETWEEN ? AND ?",
                (entity_name, start_prev.isoformat(), end_prev.isoformat()),
            )
            previous = cur.fetchone()[0]

        percent = None
        try:
            if previous == 0:
                percent = None if current == 0 else 100.0
            else:
                percent = round(((current - previous) / previous) * 100.0, 1)
        except Exception:
            percent = None

        return {"entity": entity_name, "current": current, "previous": previous, "percent_change": percent}

    def list_items(self, limit: int = 100):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT id, url, title, published, source FROM items ORDER BY id DESC LIMIT ?", (limit,))
            return cur.fetchall()

    def get_item_by_id(self, item_id: int) -> dict | None:
        with self.lock:
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
        with self.lock:
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
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT id FROM items WHERE title = ? LIMIT 1", (title,))
            return cur.fetchone() is not None

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass
