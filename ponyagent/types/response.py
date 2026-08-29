"""Agent response and token usage types."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ponyagent.types.tool import ToolCall


class TokenUsage(BaseModel):
    """Token usage statistics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @property
    def cost_usd(self) -> float | None:
        return None


class AgentResponse(BaseModel):
    """Response from an agent."""

    content: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: TokenUsage | None = None
    finish_reason: str = "stop"
