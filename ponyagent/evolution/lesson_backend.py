"""Lesson backend - records and recalls failure lessons."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Lesson(BaseModel):
    """A recorded failure lesson."""

    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex[:12])
    task: str
    error: str
    context: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class LessonBackend:
    """Stores and retrieves failure lessons.

    Prevents repeating mistakes by tracking what went wrong
    and providing context for future similar tasks.
    """

    def __init__(self) -> None:
        self._lessons: list[Lesson] = []

    def record(self, task: str, error: str, **context: Any) -> Lesson:
        """Record a failure lesson."""
        lesson = Lesson(task=task, error=error, context=context)
        self._lessons.append(lesson)
        return lesson

    def search(self, query: str, top_k: int = 5) -> list[Lesson]:
        """Search lessons by task/error text."""
        results: list[tuple[float, Lesson]] = []
        q = query.lower()

        for lesson in self._lessons:
            score = 0.0
            if q in lesson.task.lower():
                score += 2.0
            if q in lesson.error.lower():
                score += 1.0
            if score > 0:
                results.append((score, lesson))

        results.sort(key=lambda x: x[0], reverse=True)
        return [l for _, l in results[:top_k]]

    def get_recent(self, limit: int = 10) -> list[Lesson]:
        """Get most recent lessons."""
        return list(reversed(self._lessons[-limit:]))

    @property
    def count(self) -> int:
        return len(self._lessons)

    def clear(self) -> None:
        self._lessons.clear()
