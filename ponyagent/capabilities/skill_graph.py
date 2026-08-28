"""Skill graph - self-evolving skill management (Hermes + MATRIX inspired)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Skill(BaseModel):
    """A learned skill that can be applied to future tasks."""

    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex[:12])
    name: str
    description: str
    code: str = ""
    usage_count: int = 0
    success_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    last_used: datetime | None = None

    @property
    def success_rate(self) -> float:
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count


class SkillGraph:
    """Skill graph - manages learned skills and lessons.

    Implements self-evolution through:
    - Learning from successful task execution
    - Recording lessons from failures
    - Searching and applying relevant skills
    - Tracking skill effectiveness
    """

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self._lessons: list[dict[str, Any]] = []

    async def learn(
        self,
        task: str,
        result: Any,
        success: bool,
        code: str = "",
    ) -> Skill | None:
        """Learn from a task execution.

        On success: extract and store a skill.
        On failure: record a lesson.
        """
        if success:
            skill = Skill(
                name=task[:50],
                description=f"Learned from: {task[:100]}",
                code=code,
            )
            self._skills[skill.id] = skill
            return skill
        else:
            self._lessons.append(
                {
                    "task": task,
                    "error": str(result) if result else "unknown",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return None

    async def search(self, query: str, top_k: int = 5) -> list[Skill]:
        """Search skills by name/description.

        Simple substring match; can be upgraded to vector search.
        """
        results: list[tuple[float, Skill]] = []
        query_lower = query.lower()

        for skill in self._skills.values():
            score = 0.0
            if query_lower in skill.name.lower():
                score += 2.0
            if query_lower in skill.description.lower():
                score += 1.0
            if query_lower in skill.code.lower():
                score += 0.5
            if score > 0:
                results.append((score, skill))

        results.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in results[:top_k]]

    async def install(self, skill: Skill) -> bool:
        """Install a skill into the graph."""
        self._skills[skill.id] = skill
        return True

    async def get_lessons(self, task: str | None = None) -> list[dict[str, Any]]:
        """Get recorded lessons, optionally filtered by task."""
        if task:
            return [l for l in self._lessons if task in l["task"]]
        return list(self._lessons)

    def record_usage(self, skill_id: str, success: bool) -> None:
        """Record a skill usage event."""
        skill = self._skills.get(skill_id)
        if skill:
            skill.usage_count += 1
            if success:
                skill.success_count += 1
            skill.last_used = datetime.now()

    @property
    def skills(self) -> list[Skill]:
        """List all skills."""
        return list(self._skills.values())

    @property
    def skill_count(self) -> int:
        return len(self._skills)

    @property
    def lesson_count(self) -> int:
        return len(self._lessons)

    def clear(self) -> None:
        """Clear all skills and lessons."""
        self._skills.clear()
        self._lessons.clear()
