"""Message types - agent communication primitives."""

from __future__ import annotations

from typing import Literal, Any

from pydantic import BaseModel, Field

MessageRole = Literal["system", "user", "assistant", "tool"]


class Message(BaseModel):
    """A single message in an agent conversation."""

    role: MessageRole
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None
