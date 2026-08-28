"""Stub LLM adapter for testing without API keys."""

from __future__ import annotations

from ponyagent.models.base import LLMAdapter
from ponyagent.types.message import Message
from ponyagent.types.tool import ToolSpec


class StubLLMAdapter(LLMAdapter):
    """Stub LLM that returns canned responses.

    Used for testing and development without real API keys.
    """

    def __init__(self, responses: list[Message] | None = None) -> None:
        self.responses = responses or []
        self.call_count = 0
        self.name = "stub"

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
    ) -> Message:
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            return resp
        # Default: echo last user message
        last_user = ""
        for m in reversed(messages):
            if m.role == "user":
                last_user = m.content
                break
        return Message(role="assistant", content=f"[stub] {last_user}")
