"""PonyAgent - the main entry point combining all layers."""

from __future__ import annotations

import logging
from typing import Any

from ponyagent.core.agent import Agent, LLMClient
from ponyagent.core.plugin_manager import PluginManager, SharedContext
from ponyagent.types.context import RunContext

logger = logging.getLogger(__name__)


class PonyAgent:
    """Main PonyAgent class - integrates all layers.

    Combines:
    - Core: Agent with ReAct loop, EventLog, StateSerializer
    - Orchestration: 5 modes (graph, crew, turn, dag, hybrid)
    - Capabilities: tools, sandbox, permissions, skills
    - Evolution: lesson learning, experience replay
    - Models: LLM adapters (OpenAI, Stub, etc.)
    - Config: Profile/Bundle system

    Usage:
        agent = PonyAgent(
            model="gpt-4o",
            orchestrator="graph",
            evolution="skills",
        )
        result = await agent.arun("Do something")
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        *,
        api_key: str = "",
        base_url: str = "",
        orchestrator: str = "graph",
        evolution: str | list[str] | None = "skills",
        system_prompt: str = "",
        tools: list[Any] | None = None,
        max_iterations: int = 10,
        max_steps: int = 10,
        permission_gate: Any | None = None,
        profile: Any | None = None,
        llm: Any | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.orchestrator_name = orchestrator
        self.evolution_config = evolution
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.max_steps = max_steps
        self.permission_gate = permission_gate
        self.profile = profile

        # Plugin manager
        self.plugin_manager = PluginManager()
        self.ctx = self.plugin_manager.ctx

        # LLM client
        if llm is not None:
            self.llm = llm
        else:
            from ponyagent.models.stub_adapter import StubLLMAdapter
            self.llm = StubLLMAdapter()

        # Core agent (lazy - configured on arun)
        self._agent: Agent | None = None

    async def arun(self, goal: str, **kwargs: Any) -> RunContext:
        """Execute the agent with the given goal.

        Args:
            goal: The task to accomplish.
            **kwargs: Additional RunContext fields.

        Returns:
            Final RunContext with results in state.
        """
        # Resolve LLM
        llm = self.llm

        # Build the core agent
        if self._agent is None:
            self._agent = Agent(
                agent_id=f"ponyagent-{self.model}",
                llm=llm,
                max_steps=self.max_steps,
                system_prompt=self.system_prompt or (
                    "You are PonyAgent, a helpful autonomous agent."
                ),
            )

        # Run
        ctx = await self._agent.run(goal, **kwargs)
        logger.info("PonyAgent run %s complete", ctx.run_id)
        return ctx

    async def astream(self, goal: str, **kwargs: Any):
        """Stream agent execution (placeholder for now)."""
        ctx = await self.arun(goal, **kwargs)
        yield ctx

    @property
    def agent(self) -> Agent | None:
        """Access the underlying core agent."""
        return self._agent

    def info(self) -> dict[str, Any]:
        """Return agent configuration info."""
        return {
            "model": self.model,
            "orchestrator": self.orchestrator_name,
            "evolution": self.evolution_config,
            "max_steps": self.max_steps,
            "plugin_count": len(self.plugin_manager.list_plugins()),
        }
