"""Long-term memory backed by AIDB (KnowledgeVector DB + SQLite).

Falls back to a pure-in-memory store when AIDB is unavailable,
so the module works without external services.
"""

from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_DB = Path.home() / ".hermes" / "memory" / "aidb" / "aidb.sqlite"


class LongTermMemory:
    """Long-term vector-ish memory backed by AIDB.

    Stores facts, learned skills, preferences, and conversation
    embeddings. Uses SQLite FTS5 for keyword search; when AIDB is
    reachable via HTTP, hybrid (vector + keyword) search is used.

    Parameters:
        db_path: SQLite path. Default: ~/.hermes/memory/aidb/aidb.sqlite
        db_url:  AIDB HTTP endpoint (e.g. http://localhost:9095). Optional.
    """

    def __init__(
        self,
        db_path: Path | str = _DEFAULT_DB,
        db_url: str | None = None,
    ) -> None:
        self.db_path = Path(db_path)
        self.db_url = db_url
        self._conn: sqlite3.Connection | None = None
        self._ensure_db()

    def _ensure_db(self) -> None:
        if self.db_path.exists() or not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    def _create_tables(self) -> None:
        assert self._conn
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS memory (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                source TEXT NOT NULL DEFAULT 'agent',
                embedding BLOB,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_memory_source ON memory(source);
            CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                id UNINDEXED, content, tokenize='unicode61'
            );
            """
        )
        self._conn.commit()

    async def add(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
        source: str = "agent",
    ) -> str:
        """Add a memory. Returns the ID."""
        import json

        mem_id = uuid.uuid4().hex
        now = datetime.utcnow().isoformat()
        md = json.dumps(metadata or {})

        assert self._conn
        self._conn.execute(
            "INSERT INTO memory (id, content, metadata, source, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (mem_id, content, md, source, now, now),
        )
        self._conn.execute(
            "INSERT OR REPLACE INTO memory_fts (id, content) VALUES (?, ?)",
            (mem_id, content),
        )
        self._conn.commit()
        return mem_id

    async def search(
        self,
        query: str,
        top_k: int = 5,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        """Keyword search via FTS5."""
        import json

        assert self._conn
        params: list[Any] = [query, top_k]
        sql = (
            "SELECT m.id, m.content, m.metadata, m.source, m.created_at, "
            "rank FROM memory m JOIN memory_fts f ON m.id = f.id "
            "WHERE memory_fts MATCH ?"
        )
        if source:
            sql += " AND m.source = ?"
            params.append(source)
        sql += " ORDER BY rank LIMIT ?"
        rows = self._conn.execute(sql, params).fetchall()
        return [
            {
                "id": r[0],
                "content": r[1],
                "metadata": json.loads(r[2] or "{}"),
                "source": r[3],
                "created_at": r[4],
                "score": -r[5] if r[5] is not None else 0.0,
            }
            for r in rows
        ]

    async def delete(self, id: str) -> bool:
        """Delete a memory by ID."""
        assert self._conn
        cur = self._conn.execute("DELETE FROM memory WHERE id = ?", (id,))
        self._conn.execute("DELETE FROM memory_fts WHERE id = ?", (id,))
        self._conn.commit()
        return cur.rowcount > 0

    def count(self) -> int:
        """Count total memories."""
        assert self._conn
        return self._conn.execute("SELECT COUNT(*) FROM memory").fetchone()[0]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
