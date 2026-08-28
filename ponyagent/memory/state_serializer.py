"""State serializer - checkpoint and resume support.

Allows an agent run to be serialized to disk and resumed later,
enabling pause/resume semantics across process restarts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ponyagent.types.context import RunContext


class StateSerializer:
    """Serialize and deserialize RunContext state."""

    @staticmethod
    def serialize(ctx: RunContext) -> str:
        """Serialize context to JSON string."""
        return json.dumps(ctx.model_dump(), ensure_ascii=False, indent=2)

    @staticmethod
    def deserialize(data: str) -> RunContext:
        """Deserialize JSON string to RunContext."""
        return RunContext.model_validate_json(data)

    @staticmethod
    def save(ctx: RunContext, path: str | Path) -> None:
        """Save context to a file."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(StateSerializer.serialize(ctx), encoding="utf-8")

    @staticmethod
    def load(path: str | Path) -> RunContext:
        """Load context from a file."""
        p = Path(path)
        data = p.read_text(encoding="utf-8")
        return StateSerializer.deserialize(data)

    @staticmethod
    def diff(before: RunContext, after: RunContext) -> dict[str, Any]:
        """Compute state changes between two context snapshots."""
        before_state = before.state
        after_state = after.state

        changed = {}
        for key in set(before_state) | set(after_state):
            b = before_state.get(key)
            a = after_state.get(key)
            if b != a:
                changed[key] = {"from": b, "to": a}
        return changed
