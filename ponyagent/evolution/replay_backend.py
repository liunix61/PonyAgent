"""Replay backend - stores and replays past agent experiences."""

from __future__ import annotations

from typing import Any

from ponyagent.types.context import RunContext


class ReplayEntry:
    """A single replay entry."""

    def __init__(self, run_ctx: RunContext, outcome: str, score: float) -> None:
        self.run_ctx = run_ctx
        self.outcome = outcome
        self.score = score

    def __repr__(self) -> str:
        return f"ReplayEntry(outcome={self.outcome}, score={self.score})"


class ReplayBackend:
    """Stores successful/failed runs for replay and analysis.

    Enables learning from experience by:
    - Recording complete run contexts
    - Rating outcomes
    - Retrieving similar past runs
    """

    def __init__(self) -> None:
        self._entries: list[ReplayEntry] = []

    def record(self, ctx: RunContext, outcome: str, score: float = 0.0) -> ReplayEntry:
        """Record a run experience."""
        entry = ReplayEntry(run_ctx=ctx, outcome=outcome, score=score)
        self._entries.append(entry)
        return entry

    def search(self, goal: str, top_k: int = 5) -> list[ReplayEntry]:
        """Find similar past runs by goal."""
        goal_lower = goal.lower()
        scored: list[tuple[float, ReplayEntry]] = []

        for entry in self._entries:
            run_goal = entry.run_ctx.state.get("goal", "")
            if goal_lower in run_goal.lower():
                score = entry.score
            elif any(goal_lower in str(v).lower() for v in entry.run_ctx.state.values()):
                score = entry.score * 0.5
            else:
                continue
            scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:top_k]]

    def get_by_outcome(self, outcome: str) -> list[ReplayEntry]:
        """Get all runs with a specific outcome."""
        return [e for e in self._entries if e.outcome == outcome]

    @property
    def success_rate(self) -> float:
        if not self._entries:
            return 0.0
        successes = sum(1 for e in self._entries if e.outcome == "success")
        return successes / len(self._entries)

    @property
    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
