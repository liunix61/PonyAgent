"""Run context - execution state container."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class RunContext(BaseModel):
    """Execution context for an agent run.

    Contains run identity, agent identity, parent linkage, and mutable state.
    """

    run_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    agent_id: str
    parent_run_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    state: dict[str, Any] = Field(default_factory=dict)
    step: int = 0

    def advance(self) -> None:
        """Increment the step counter."""
        self.step += 1
