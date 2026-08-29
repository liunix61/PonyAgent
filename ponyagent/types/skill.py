"""Skill type for SkillGraph."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Skill(BaseModel):
    """A learnable skill."""

    id: str
    name: str
    description: str
    code: str
    input_schema: dict | None = None
    output_schema: dict | None = None
    vector: list[float] | None = None
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    tags: list[str] = Field(default_factory=list)

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total
