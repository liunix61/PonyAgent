"""Shared blackboard for inter-agent communication."""

from __future__ import annotations

from typing import Any


class Blackboard:
    """Shared blackboard for agent collaboration.

    Provides a shared key-value store where agents can
    read and write during orchestration.
    """

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._writers: dict[str, list[str]] = {}

    def write(self, key: str, value: Any, writer: str = "anonymous") -> None:
        """Write a value to the blackboard."""
        self._data[key] = value
        self._writers.setdefault(writer, []).append(key)

    def read(self, key: str, default: Any = None) -> Any:
        """Read a value from the blackboard."""
        return self._data.get(key, default)

    def keys(self) -> list[str]:
        """List all keys."""
        return list(self._data.keys())

    def clear(self) -> None:
        """Clear the blackboard."""
        self._data.clear()
        self._writers.clear()

    def get_writer(self, key: str) -> str | None:
        """Find who wrote a given key."""
        for writer, keys in self._writers.items():
            if key in keys:
                return writer
        return None
