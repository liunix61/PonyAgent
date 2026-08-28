"""Event log - append-only event log (Log-as-Truth).

Every action the agent takes is recorded as an event.
The full history of an agent run can be replayed from the log.
"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """A single event in the event log."""

    timestamp: float = Field(default_factory=time.time)
    run_id: str
    event_type: str
    data: dict[str, Any] = Field(default_factory=dict)


class EventLog:
    """Append-only event log for an agent run.

    All actions are recorded as events.
    Context is projected from the log, not stored separately.
    """

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self._entries: list[LogEntry] = []

    def append(self, event_type: str, **data: Any) -> LogEntry:
        """Append an event to the log."""
        entry = LogEntry(run_id=self.run_id, event_type=event_type, data=data)
        self._entries.append(entry)
        return entry

    def entries(self) -> list[LogEntry]:
        """Return all entries."""
        return list(self._entries)

    def last(self) -> LogEntry | None:
        """Return the most recent entry, or None if empty."""
        if not self._entries:
            return None
        return self._entries[-1]

    def find(self, event_type: str) -> list[LogEntry]:
        """Find all entries of a given event type."""
        return [e for e in self._entries if e.event_type == event_type]

    def __len__(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        """Clear the log."""
        self._entries.clear()
