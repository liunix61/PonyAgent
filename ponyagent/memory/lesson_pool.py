"""Lesson pool - persistent record of past errors (memory layer)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ponyagent.types.lesson import Lesson

_DEFAULT_PATH = Path.home() / ".hermes" / "memory" / "lessons.json"


class LessonPool:
    """Persistent lesson pool (JSON file).

    Bridges the gap between the evolution layer's LessonBackend
    (in-process) and a durable cross-session store.
    """

    def __init__(self, path: Path | str = _DEFAULT_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lessons: list[Lesson] = self._load()

    def _load(self) -> list[Lesson]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return [Lesson.model_validate(x) for x in raw]
        except (json.JSONDecodeError, Exception):
            return []

    def _save(self) -> None:
        self.path.write_text(
            json.dumps([l.model_dump(mode="json") for l in self._lessons],
                       ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    def add(self, lesson: Lesson) -> None:
        self._lessons.append(lesson)
        self._save()

    def get_all(self) -> list[Lesson]:
        return list(self._lessons)

    def search(self, query: str) -> list[Lesson]:
        q = query.lower()
        return [
            l for l in self._lessons
            if q in l.task.lower() or q in l.error.lower()
        ]

    def count(self) -> int:
        return len(self._lessons)

    def clear(self) -> None:
        self._lessons = []
        self._save()
