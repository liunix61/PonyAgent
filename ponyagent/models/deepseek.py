"""DeepSeek adapter (OpenAI-compatible)."""

from __future__ import annotations

from ponyagent.models.openai_adapter import OpenAIAdapter


class DeepSeekAdapter(OpenAIAdapter):
    """DeepSeek API adapter - extends OpenAI adapter."""

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com/v1",
    ) -> None:
        super().__init__(api_key=api_key, model=model, base_url=base_url)
