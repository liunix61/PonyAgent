"""Protocol definitions shared across layers."""

from __future__ import annotations

from typing import Any, AsyncIterator, Protocol

from ponyagent.types.context import RunContext
from ponyagent.types.message import Message
from ponyagent.types.response import AgentResponse


class MemoryBackend(Protocol):
    """Memory backend protocol."""

    async def add(self, content: str, metadata: dict[str, Any] | None = None) -> str:
        """Add content to memory, return ID."""
        ...

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Search memory."""
        ...

    async def delete(self, id: str) -> bool:
        """Delete by ID."""
        ...


class ContextProtocol(Protocol):
    """Shared context protocol."""

    def get(self, key: str, default: Any = None) -> Any: ...
    def register(self, plugin: str, key: str, value: Any) -> Any: ...
    async def rollback(self, plugin: str) -> None: ...


class LLMProtocol(Protocol):
    """LLM protocol for model adapters."""

    async def complete(
        self,
        messages: list[Message],
        *,
        tools: list[dict] | None = None,
    ) -> Message:
        ...

    def model_name(self) -> str:
        ...
