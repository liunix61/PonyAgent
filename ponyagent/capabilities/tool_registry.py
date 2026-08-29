"""Tool registry - central tool management."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from ponyagent.types.tool import ToolResult, ToolSpec

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for tools (DeepSeek Harness-style)."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._handlers: dict[str, Callable] = {}

    def register(self, spec: ToolSpec, handler: Callable | None = None) -> None:
        """Register a tool spec and optional handler."""
        self._tools[spec.name] = spec
        if handler:
            self._handlers[spec.name] = handler

    def register_fn(self, fn: Callable, name: str | None = None, description: str = "") -> None:
        """Register a function as a tool."""
        tool_name = name or fn.__name__
        spec = ToolSpec(
            name=tool_name,
            description=description or fn.__doc__ or "",
            parameters={},
            fn=fn,
        )
        self._tools[tool_name] = spec
        self._handlers[tool_name] = fn

    async def invoke(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Invoke a tool by name."""
        handler = self._handlers.get(name)
        if handler is None:
            return ToolResult(tool_call_id="", name=name, status="error", error=f"Tool not found: {name}")
        try:
            result = handler(**arguments)
            if asyncio.iscoroutine(result):
                result = await result
            return ToolResult(tool_call_id="", name=name, status="success", output=str(result))
        except Exception as e:
            return ToolResult(tool_call_id="", name=name, status="error", error=str(e))

    def list_tools(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def remove(self, name: str) -> bool:
        self._tools.pop(name, None)
        self._handlers.pop(name, None)
        return True
