"""Short-term memory - in-process sliding window."""

from __future__ import annotations

from collections import deque
from typing import Any

from ponyagent.types.message import Message


class ShortTermMemory:
    """In-process short-term memory with a sliding window.

    Holds recent messages for the current conversation/session.
    When the window fills, oldest messages are dropped (FIFO).

    Design: process-local, no persistence. Fast, no I/O.
    """

    def __init__(self, max_messages: int = 50, max_tokens: int = 8000) -> None:
        self._max_messages = max_messages
        self._max_tokens = max_tokens
        self._messages: deque[Message] = deque(maxlen=max_messages)
        self._token_budget = 0

    @property
    def messages(self) -> list[Message]:
        return list(self._messages)

    @property
    def size(self) -> int:
        return len(self._messages)

    @property
    def token_budget(self) -> int:
        return self._token_budget

    def add(self, message: Message) -> None:
        """Add a message to short-term memory."""
        tokens = self._estimate_tokens(message)
        self._messages.append(message)
        self._token_budget += tokens

        # Evict from the front if over token budget
        while self._token_budget > self._max_tokens and len(self._messages) > 1:
            oldest = self._messages.popleft()
            self._token_budget -= self._estimate_tokens(oldest)

    def clear(self) -> None:
        self._messages.clear()
        self._token_budget = 0

    def to_list(self) -> list[dict[str, Any]]:
        """Return messages as a list of dicts."""
        return [m.model_dump() for m in self._messages]

    @staticmethod
    def _estimate_tokens(message: Message) -> int:
        """Rough token estimate: ~1 token per 4 chars."""
        return max(1, len(message.content) // 4)
