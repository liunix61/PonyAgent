"""Base LLM adapter protocol."""

from __future__ import annotations

from ponyagent.types.message import Message


class LLMAdapter:
    """Base class for LLM adapters.

    Subclass to integrate with specific LLM providers.
    Override `complete` for production use.
    """

    name: str = "base"

    async def complete(
        self,
        messages: list[Message],
        *,
        tools: list | None = None,
    ) -> Message:
        """Generate the next assistant message.

        Args:
            messages: Conversation history.
            tools: Available tools for the model to call.

        Returns:
            The assistant's response message.
        """
        raise NotImplementedError

    def model_name(self) -> str:
        """Return the model identifier."""
        return self.name
