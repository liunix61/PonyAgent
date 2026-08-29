"""Application configuration (Pydantic Settings-style)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings."""

    # LLM
    model: str = "gpt-4o"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    max_tokens: int = 4096
    temperature: float = 0.7

    # Agent
    max_steps: int = 10
    orchestrator: str = "graph"
    evolution: str | None = None

    # Memory
    short_term_size: int = 50
    aidb_path: str = "~/.hermes/memory/aidb/aidb.sqlite"
    aimem_path: str = "~/.hermes/memory/aimem/episodic.json"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    @classmethod
    def from_env(cls) -> "Settings":
        """Load from environment variables."""
        import os

        return cls(
            model=os.getenv("PONY_MODEL", "gpt-4o"),
            api_key=os.getenv("PONY_API_KEY", ""),
            base_url=os.getenv("PONY_BASE_URL", "https://api.openai.com/v1"),
        )
