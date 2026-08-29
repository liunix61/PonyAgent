"""Session event types for EventLog."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from ponyagent.types.message import Message, MessageRole

SessionEventType = Literal[
    "user/message",
    "assistant/message",
    "tool/call",
    "tool/result",
    "turn/start",
    "turn/end",
    "turn/complete",
    "agent/start",
    "agent/end",
]


class SessionEvent(BaseModel):
    """Session event - appended to EventLog."""

    type: SessionEventType
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    def to_message(self) -> Message | None:
        """Project as Message (only for message events)."""
        if self.type not in ("user/message", "assistant/message"):
            return None
        role = "user" if self.type == "user/message" else "assistant"
        content = self.data.get("content", "")
        return Message(role=role, content=content)
