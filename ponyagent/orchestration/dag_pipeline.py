"""DAGPipelineOrchestrator - DAG-based pipeline (MATRIX 3.0-style).

Supports multiple execution modes: pipeline, roundtable,
hierarchical, parallel, and debate.
"""

from __future__ import annotations

from ponyagent.types.orchestration import (
    Edge,
    OrchestratorEvent,
    OrchestratorState,
)


class DAGPipelineOrchestrator:
    """MATRIX-style DAG pipeline orchestrator.

    Executes nodes in topological order with configurable
    collaboration modes:
    - pipeline: sequential execution
    - roundtable: all nodes see previous outputs
    - hierarchical: parent delegates to children
    - parallel: independent nodes run concurrently
    - debate: nodes argue positions
    """

    def __init__(
        self,
        nodes: list[str],
        edges: list[Edge],
        mode: str = "pipeline",
    ) -> None:
        self.nodes = nodes
        self.edges = edges
        self.mode = mode

    async def arun(self, state: OrchestratorState) -> OrchestratorState:
        """Execute the DAG pipeline."""
        if self.mode == "pipeline":
            await self._run_pipeline(state)
        elif self.mode == "roundtable":
            await self._run_roundtable(state)
        elif self.mode == "parallel":
            await self._run_parallel(state)
        elif self.mode == "debate":
            await self._run_debate(state)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
        return state

    async def _run_pipeline(self, state: OrchestratorState) -> None:
        """Sequential execution following DAG order."""
        order = self._topological_sort()
        for name in order:
            state.current_node = name
            state.add_message("assistant", f"[{name}] Pipeline step")
            state.set(f"{name}_output", f"Pipeline: {name}")
            state.completed_nodes.append(name)
        state.current_node = None

    async def _run_roundtable(self, state: OrchestratorState) -> None:
        """All nodes see previous outputs."""
        for name in self.nodes:
            prev_outputs = [
                state.get(f"{n}_output", "")
                for n in self.nodes if n != name
            ]
            state.current_node = name
            context = f"Previous: {prev_outputs}"
            state.add_message("assistant", f"[{name}] Roundtable: {context}")
            state.set(f"{name}_output", f"Roundtable: {name}")
            state.completed_nodes.append(name)
        state.current_node = None

    async def _run_parallel(self, state: OrchestratorState) -> None:
        """Independent nodes execute in 'parallel' (simulated)."""
        for name in self.nodes:
            state.current_node = name
            state.add_message("assistant", f"[{name}] Parallel execution")
            state.set(f"{name}_output", f"Parallel: {name}")
            state.completed_nodes.append(name)
        state.current_node = None

    async def _run_debate(self, state: OrchestratorState) -> None:
        """Nodes debate positions."""
        positions: dict[str, str] = {}
        for name in self.nodes:
            state.current_node = name
            position = f"{name} argues for their position"
            positions[name] = position
            state.add_message("assistant", f"[{name}] Debate: {position}")
            state.set(f"{name}_position", position)
            state.completed_nodes.append(name)
        state.current_node = None

    def _topological_sort(self) -> list[str]:
        """Sort nodes by DAG dependencies."""
        order: list[str] = []
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visited:
                return
            visited.add(node)
            for edge in self.edges:
                if edge.source == node:
                    visit(edge.target)
            order.insert(0, node)

        for node in self.nodes:
            if node not in visited:
                visit(node)

        return order

    async def astream(self, state: OrchestratorState):
        """Stream DAG events."""
        yield OrchestratorEvent(node="dag", event_type="start", data={"mode": self.mode})
        await self.arun(state)
        yield OrchestratorEvent(node="dag", event_type="complete")

    def get_graph(self) -> list[Edge]:
        """Return the DAG edges."""
        return list(self.edges)
