"""FastAPI HTTP API for PonyAgent."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from ponyagent import PonyAgent
from ponyagent.models.stub_adapter import StubLLMAdapter


class RunRequest(BaseModel):
    """Request body for running an agent."""

    goal: str
    model: str = "gpt-4o"
    orchestrator: str = "graph"
    max_steps: int = 10


class RunResponse(BaseModel):
    """Response from an agent run."""

    run_id: str
    steps: int
    content: str
    state: dict[str, Any] = Field(default_factory=dict)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="PonyAgent API",
        version="0.1.0",
        description="Lightweight multi-agent operating system",
    )

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"name": "PonyAgent", "version": "0.1.0", "status": "ok"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.post("/run", response_model=RunResponse)
    async def run(req: RunRequest) -> RunResponse:
        llm = StubLLMAdapter()
        agent = PonyAgent(
            model=req.model,
            llm=llm,
            orchestrator=req.orchestrator,
            max_steps=req.max_steps,
        )
        ctx = await agent.arun(req.goal)
        return RunResponse(
            run_id=ctx.run_id,
            steps=ctx.step,
            content=ctx.state.get("final_content", ""),
            state=ctx.state,
        )

    return app


# Module-level app for uvicorn
app = create_app()
