"""CrewOrchestrator - role-based collaboration (CrewAI-style).

Agents with defined roles collaborate on a shared goal.
Supports sequential and hierarchical processes.
"""

from __future__ import annotations

from ponyagent.types.orchestration import (
    OrchestratorEvent,
    OrchestratorState,
    Role,
)


class CrewOrchestrator:
    """CrewAI-style role collaboration orchestrator.

    Each role has a goal, backstory, and tools.
    Roles execute sequentially by default, with optional
    hierarchical (manager delegates) mode.
    """

    def __init__(self, roles: list[Role], process: str = "sequential") -> None:
        self.roles = roles
        self.process = process

    async def arun(self, state: OrchestratorState) -> OrchestratorState:
        """Execute the crew."""
        if self.process == "sequential":
            await self._run_sequential(state)
        elif self.process == "hierarchical":
            await self._run_hierarchical(state)
        else:
            raise ValueError(f"Unknown process: {self.process}")
        return state

    async def _run_sequential(self, state: OrchestratorState) -> None:
        """Run roles sequentially, each contributing to shared state."""
        for role in self.roles:
            state.current_node = role.name
            role_output = state.state.get(f"{role.name}_output", "")
            state.set(
                f"{role.name}_output",
                f"Role {role.name} executed (goal: {role.goal}). Previous: {role_output}",
            )
            state.add_message("assistant", f"[{role.name}] Executed: {role.goal}")
            state.completed_nodes.append(role.name)

    async def _run_hierarchical(self, state: OrchestratorState) -> None:
        """Run with a manager role delegating to others."""
        manager = self.roles[0] if self.roles else None
        workers = self.roles[1:] if len(self.roles) > 1 else []

        if manager:
            state.current_node = manager.name
            state.add_message("assistant", f"[{manager.name}] Delegating to {len(workers)} workers")
            state.completed_nodes.append(manager.name)

        for worker in workers:
            state.current_node = worker.name
            state.add_message("assistant", f"[{worker.name}] Working on: {worker.goal}")
            state.set(f"{worker.name}_output", f"Completed: {worker.goal}")
            state.completed_nodes.append(worker.name)

        state.current_node = None

    async def astream(self, state: OrchestratorState):
        """Stream crew events."""
        yield OrchestratorEvent(node="crew", event_type="start")

        if self.process == "sequential":
            await self._run_sequential(state)
        else:
            await self._run_hierarchical(state)

        for role in self.roles:
            yield OrchestratorEvent(node=role.name, event_type="complete")

        yield OrchestratorEvent(node="crew", event_type="complete")

    def get_graph(self) -> None:
        """Crew mode has no explicit DAG."""
        return None
