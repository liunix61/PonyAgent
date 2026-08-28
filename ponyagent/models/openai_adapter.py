"""OpenAI-compatible LLM adapter."""

from __future__ import annotations

import json
from typing import Any

import httpx

from ponyagent.models.base import LLMAdapter
from ponyagent.types.message import Message
from ponyagent.types.tool import ToolSpec


class OpenAIAdapter(LLMAdapter):
    """OpenAI-compatible API adapter.

    Works with any OpenAI-compatible endpoint (OpenAI, DeepSeek,
    local LLMs via vLLM/Ollama, etc.)
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.name = model

    def model_name(self) -> str:
        return self.model

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
    ) -> Message:
        """Call the OpenAI-compatible API."""
        if not self.api_key:
            raise ValueError(
                "API key not set. Pass api_key to OpenAIAdapter "
                "or set OPENAI_API_KEY env var."
            )

        api_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": api_messages,
        }

        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]["message"]
        return Message(
            role="assistant",
            content=choice.get("content", ""),
            tool_calls=choice.get("tool_calls"),
        )
