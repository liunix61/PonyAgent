"""Tool types - tool definition and invocation."""

from __future__ import annotations

from typing import Any, Literal, Callable

from pydantic import BaseModel, Field


class ToolSpec(BaseModel):
    """Specification of a callable tool."""

    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    fn: Callable | None = None

    def invoke(self, **kwargs: Any) -> Any:
        """Invoke the tool function with the given arguments."""
        if self.fn is None:
            raise ValueError(f"Tool '{self.name}' has no callable")
        return self.fn(**kwargs)


class ToolCall(BaseModel):
    """A request to call a tool."""

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Result of a tool invocation."""

    tool_call_id: str
    name: str
    status: Literal["success", "error"] = "success"
    output: str | None = None
    error: str | None = None
