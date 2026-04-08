import os
import json
import sqlite3
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, HTTPServer

CONFIG_NAME = "config.yaml"
DEFAULT_DB = "watcher.db"


def _resolve_db_path() -> Path:
    if Path(CONFIG_NAME).exists():
        try:
            import yaml
            cfg = yaml.safe_load(Path(CONFIG_NAME).read_text(encoding="utf-8")) or {}
            sqlite_path = cfg.get("sqlite_path", cfg.get("database", DEFAULT_DB))
            p = Path(sqlite_path)
            if not p.is_absolute():
                p = Path.cwd() / p
            return p
        except Exception:
            pass
    return Path.cwd() / DEFAULT_DB


def get_article_count_from_db():
    db_path = _resolve_db_path()
    if not db_path.exists():
        return 0
    try:
        with sqlite3.connect(str(db_path)) as conn:
            return conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    except Exception:
        return 0


def get_feed_count_from_config():
    config_file = Path(CONFIG_NAME)
    if not config_file.exists():
        return 0
    try:
        import yaml
        cfg = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
        feeds = cfg.get("feeds", [])
        if isinstance(feeds, dict):
            return len(feeds)
        return len(feeds) if feeds else 0
    except Exception:
        return 0


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/article-count"):
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            data = {
                "articles": get_article_count_from_db(),
                "feeds": get_feed_count_from_config()
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return
        
        if self.path.startswith("/api/recent-articles"):
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            db_path = _resolve_db_path()
            articles = []
            if db_path.exists():
                try:
                    with sqlite3.connect(str(db_path)) as conn:
                        conn.row_factory = sqlite3.Row
                        rows = conn.execute("SELECT title, source, published, summary, url FROM items ORDER BY id DESC LIMIT 10").fetchall()
                        articles = [dict(row) for row in rows]
                except Exception:
                    pass
            self.wfile.write(json.dumps(articles).encode("utf-8"))
            return
        return super().do_GET()


def run(server_class=HTTPServer, handler_class=DashboardHandler, port=5000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Serving on http://localhost:{port}")
    print("Open http://localhost:5000/index.html")
    httpd.serve_forever()


if __name__ == '__main__':
    run()
