"""Lesson type for LessonBackend."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Lesson(BaseModel):
    """A recorded lesson from a failure or success."""

    id: str
    task: str
    error: str
    context: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    tags: list[str] = Field(default_factory=list)
    resolved: bool = False
