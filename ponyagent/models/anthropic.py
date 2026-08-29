"""Anthropic Claude adapter."""

from __future__ import annotations

import httpx

from ponyagent.models.base import LLMAdapter
from ponyagent.types.message import Message


class AnthropicAdapter(LLMAdapter):
    """Anthropic Claude API adapter."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        base_url: str = "https://api.anthropic.com",
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    def model_name(self) -> str:
        return self._model

    async def complete(
        self,
        messages: list[Message],
        *,
        tools: list[dict] | None = None,
    ) -> Message:
        if not self._api_key:
            raise ValueError("Anthropic API key is required")

        system_prompt = ""
        api_messages = []
        for m in messages:
            if m.role == "system":
                system_prompt += m.content + "\n"
            else:
                api_messages.append({"role": m.role, "content": m.content})

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body: dict[str, object] = {
            "model": self._model,
            "max_tokens": 1024,
            "messages": api_messages,
        }
        if system_prompt:
            body["system"] = system_prompt
        if tools:
            body["tools"] = tools

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base_url}/v1/messages",
                headers=headers,
                json=body,
                timeout=60.0,
            )
        resp.raise_for_status()
        data = resp.json()
        return Message(role="assistant", content=data.get("content", [{}])[0].get("text", ""))
