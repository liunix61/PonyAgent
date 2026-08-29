"""PonyAgent - the main entry point combining all layers."""

from __future__ import annotations

import logging
from typing import Any

from ponyagent.capabilities.skill_graph import SkillGraph
from ponyagent.capabilities.tool_registry import ToolRegistry
from ponyagent.core.agent import Agent, LLMClient
from ponyagent.core.plugin_manager import PluginManager, SharedContext
from ponyagent.evolution.hermes_backend import HermesSkillBackend
from ponyagent.evolution.lesson_backend import LessonBackend
from ponyagent.evolution.memory_backend import UniAgentsMemoryBackend
from ponyagent.evolution.matrix_backend import MatrixCodeBackend
from ponyagent.evolution.protocol import EvolutionProtocol
from ponyagent.evolution.replay_backend import ReplayBackend
from ponyagent.memory.episodic import EpisodicMemory
from ponyagent.memory.event_log import EventLog
from ponyagent.memory.lesson_pool import LessonPool
from ponyagent.memory.long_term import LongTermMemory
from ponyagent.memory.short_term import ShortTermMemory
from ponyagent.memory.state_serializer import StateSerializer
from ponyagent.models.base import LLMAdapter
from ponyagent.models.stub_adapter import StubLLMAdapter
from ponyagent.types.context import RunContext
from ponyagent.types.message import Message
from ponyagent.types.skill import Skill

logger = logging.getLogger(__name__)

_EVOLUTION_BACKENDS: dict[str, type[EvolutionProtocol]] = {
    "hermes_skills": HermesSkillBackend,
    "matrix_codegen": MatrixCodeBackend,
    "uniagents_memory": UniAgentsMemoryBackend,
    "replay": ReplayBackend,
    "lesson_pool": LessonBackend,
    "skills": SkillGraph,
}


class PonyAgent:
    """Main PonyAgent class - integrates all 7 layers.

    Usage:
        agent = PonyAgent(
            model="gpt-4o",
            orchestrator="graph",
            evolution="hermes_skills",
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
        evolution: str | list[str] | None = None,
        system_prompt: str = "",
        tools: list[Any] | None = None,
        max_iterations: int = 10,
        max_steps: int = 10,
        permission_gate: Any | None = None,
        profile: Any | None = None,
        llm: Any | None = None,
        short_term_size: int = 50,
        aidb_path: str | None = None,
        aimem_path: str | None = None,
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

        # Plugin manager (kernel layer)
        self.plugin_manager = PluginManager()
        self.ctx: SharedContext = self.plugin_manager.ctx

        # LLM client (models layer)
        if llm is not None:
            self.llm = llm
        elif api_key:
            from ponyagent.models.openai_adapter import OpenAIAdapter
            self.llm = OpenAIAdapter(model=model, api_key=api_key, base_url=base_url)
        else:
            self.llm = StubLLMAdapter()

        # Tools registry (capabilities layer)
        self.tool_registry = ToolRegistry()
        for t in tools or []:
            self.tool_registry.register_fn(t)

        # Memory (memory layer)
        self.short_term: ShortTermMemory = ShortTermMemory(max_messages=short_term_size)
        self.long_term: LongTermMemory = LongTermMemory(db_path=aidb_path) if aidb_path else LongTermMemory()
        self.episodic: EpisodicMemory = EpisodicMemory(path=aimem_path) if aimem_path else EpisodicMemory()
        self.lesson_pool: LessonPool = LessonPool()
        self.event_log: EventLog = EventLog(run_id="ponyagent")
        self.state_serializer: StateSerializer = StateSerializer()

        # Evolution (evolution layer)
        self.evolutions: list[EvolutionProtocol] = []
        if evolution:
            names = [evolution] if isinstance(evolution, str) else list(evolution)
            for name in names:
                backend_cls = _EVOLUTION_BACKENDS.get(name)
                if backend_cls:
                    if name == "hermes_skills":
                        self.evolutions.append(HermesSkillBackend())
                    elif name == "uniagents_memory":
                        self.evolutions.append(UniAgentsMemoryBackend())
                    elif name == "matrix_codegen":
                        self.evolutions.append(MatrixCodeBackend())
                    elif name == "replay":
                        self.evolutions.append(ReplayBackend())
                    elif name == "lesson_pool":
                        self.evolutions.append(LessonBackend())
                    elif name == "skills":
                        self.evolutions.append(SkillGraph())

        # Core agent (lazy)
        self._agent: Agent | None = None

    async def arun(self, goal: str, **kwargs: Any) -> RunContext:
        """Execute the agent with the given goal.

        Persists the goal and final result to memory + evolution.
        """
        # Record user message to short-term + event log
        user_msg = Message(role="user", content=goal)
        self.short_term.add(user_msg)

        # Build core agent
        if self._agent is None:
            self._agent = Agent(
                agent_id=f"ponyagent-{self.model}",
                llm=self.llm,
                max_steps=self.max_steps,
                system_prompt=self.system_prompt or "You are PonyAgent, a helpful autonomous agent.",
            )

        # Run
        ctx = await self._agent.run(goal, **kwargs)
        final_content = ctx.state.get("final_content", "")
        logger.info("PonyAgent run %s complete (steps=%d)", ctx.run_id, ctx.step)

        # Record assistant message
        if final_content:
            self.short_term.add(Message(role="assistant", content=final_content))

        # Persist to long-term memory
        try:
            await self.long_term.add(
                content=f"[{self.orchestrator_name}] {goal} -> {final_content[:500]}",
                metadata={"goal": goal, "steps": ctx.step, "orchestrator": self.orchestrator_name},
                source="ponyagent",
            )
        except Exception as e:
            logger.warning("long_term persist failed: %s", e)

        # Record episodic memory
        try:
            self.episodic.add(
                content=f"{goal} -> {final_content[:200]}",
                tags=["task", self.orchestrator_name],
                metadata={"goal": goal, "steps": ctx.step, "run_id": ctx.run_id},
            )
        except Exception as e:
            logger.warning("episodic persist failed: %s", e)

        # Run evolution backends (learn from execution)
        for backend in self.evolutions:
            try:
                await backend.learn(goal, final_content, success=bool(final_content))
            except Exception as e:
                logger.warning("evolution backend failed: %s", e)

        return ctx

    async def astream(self, goal: str, **kwargs: Any):
        """Stream agent execution."""
        ctx = await self.arun(goal, **kwargs)
        yield ctx

    @property
    def agent(self) -> Agent | None:
        """Access the underlying core agent."""
        return self._agent

    def install_skill(self, skill: Skill) -> list[bool]:
        """Install a skill into all evolution backends that support it."""
        results = []
        for backend in self.evolutions:
            try:
                import asyncio
                results.append(asyncio.run(backend.install(skill)))
            except Exception:
                results.append(False)
        return results

    def info(self) -> dict[str, Any]:
        """Return agent configuration info."""
        return {
            "model": self.model,
            "orchestrator": self.orchestrator_name,
            "evolution": self.evolution_config,
            "max_steps": self.max_steps,
            "plugin_count": len(self.plugin_manager.list_plugins()),
            "evolution_backends": len(self.evolutions),
            "short_term_size": self.short_term.size,
            "episodic_count": self.episodic.count(),
        }
