"""Episodic memory backed by AIMEM.

AIMEM is a JSONL file (~/.hermes/memory/aimem/episodic.json)
that records dated, tagged episodes for cross-session recall.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

_DEFAULT_PATH = Path.home() / ".hermes" / "memory" / "aimem" / "episodic.json"


class EpisodicMemory:
    """Episodic memory (AIMEM).

    Each episode: {timestamp, tags, content, metadata}
    Appended as JSONL-ish (list). Read in whole; suitable for
    medium-sized episodes (hundreds, not millions).
    """

    def __init__(self, path: Path | str = _DEFAULT_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def _save(self, episodes: list[dict[str, Any]]) -> None:
        self.path.write_text(
            json.dumps(episodes, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add(
        self,
        content: str,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        episode = {
            "timestamp": datetime.utcnow().isoformat(),
            "content": content,
            "tags": tags or [],
            "metadata": metadata or {},
        }
        episodes = self._load()
        episodes.append(episode)
        self._save(episodes)
        return episode

    def search(
        self,
        query: str,
        tags: list[str] | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        episodes = self._load()
        q = query.lower()
        results = []
        for ep in episodes:
            content = ep.get("content", "").lower()
            score = content.count(q) if q else 0
            if tags and any(t not in ep.get("tags", []) for t in tags):
                continue
            if score > 0 or not query:
                results.append((score, ep))
        results.sort(key=lambda x: -x[0])
        return [ep for _, ep in results[:top_k]]

    def count(self) -> int:
        return len(self._load())

    def clear(self) -> None:
        self._save([])
