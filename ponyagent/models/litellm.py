"""LiteLLM gateway adapter (unified multi-provider)."""

from __future__ import annotations

import httpx

from ponyagent.models.base import LLMAdapter
from ponyagent.types.message import Message


class LiteLLMAdapter(LLMAdapter):
    """LiteLLM proxy adapter - routes to any model via a single endpoint."""

    def __init__(
        self,
        api_key: str = "",
        model: str = "gpt-4o",
        base_url: str = "https://api.litellm.ai/",
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
            raise ValueError("LiteLLM API key is required")

        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        body: dict[str, object] = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if tools:
            body["tools"] = tools

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=body,
                timeout=60.0,
            )
        resp.raise_for_status()
        data = resp.json()
        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        return Message(
            role="assistant",
            content=msg.get("content", ""),
            tool_calls=msg.get("tool_calls"),
        )
