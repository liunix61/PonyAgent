"""StateGraphOrchestrator - graph state machine (LangGraph-style).

Supports nodes, directed edges, conditional routing, and
topological execution order.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Callable

from ponyagent.types.orchestration import (
    Edge,
    OrchestratorEvent,
    OrchestratorState,
)


class StateGraphOrchestrator:
    """LangGraph-style state machine orchestrator.

    Nodes are callables that transform OrchestratorState.
    Edges define execution order, optionally with conditions.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, Callable] = {}
        self._edges: list[Edge] = []
        self._entry_point: str | None = None
        self._end_nodes: set[str] = set()

    def add_node(self, name: str, fn: Callable) -> None:
        """Add a node (callable) to the graph."""
        self._nodes[name] = fn

    def add_edge(self, source: str, target: str, condition: str | None = None) -> None:
        """Add a directed edge between nodes."""
        self._edges.append(Edge(source=source, target=target, condition=condition))

    def set_entry_point(self, name: str) -> None:
        """Set the entry node."""
        self._entry_point = name

    def set_end(self, name: str) -> None:
        """Mark a node as a terminal node."""
        self._end_nodes.add(name)

    def _get_outgoing(self, node: str) -> list[Edge]:
        return [e for e in self._edges if e.source == node]

    def _topological_sort(self) -> list[str]:
        """Return nodes in topological order."""
        graph: dict[str, set[str]] = defaultdict(set)
        in_degree: dict[str, int] = defaultdict(int)

        for name in self._nodes:
            in_degree.setdefault(name, 0)

        for edge in self._edges:
            if edge.target not in graph[edge.source]:
                in_degree[edge.target] += 1
            graph[edge.source].add(edge.target)

        queue = deque([n for n, d in in_degree.items() if d == 0])
        order: list[str] = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return order

    async def arun(self, state: OrchestratorState) -> OrchestratorState:
        """Execute the graph."""
        if not self._entry_point:
            raise ValueError("No entry point set")

        node_order = self._topological_sort()
        entry_idx = node_order.index(self._entry_point) if self._entry_point in node_order else 0

        for name in node_order[entry_idx:]:
            state.current_node = name
            fn = self._nodes[name]
            result = fn(state)
            if hasattr(result, "__await__"):
                await result
            state.completed_nodes.append(name)

            if name in self._end_nodes:
                break

        state.current_node = None
        return state

    async def astream(self, state: OrchestratorState):
        """Stream events as the graph executes."""
        yield OrchestratorEvent(node="graph", event_type="start")

        if not self._entry_point:
            yield OrchestratorEvent(node="graph", event_type="error", data={"error": "No entry point"})
            return

        node_order = self._topological_sort()
        entry_idx = node_order.index(self._entry_point) if self._entry_point in node_order else 0

        for name in node_order[entry_idx:]:
            yield OrchestratorEvent(node=name, event_type="enter")

            if name in self._end_nodes:
                yield OrchestratorEvent(node=name, event_type="end")
                break
            if name not in self._nodes:
                continue

            fn = self._nodes[name]
            result = fn(state)
            if hasattr(result, "__await__"):
                await result

            yield OrchestratorEvent(node=name, event_type="exit")
            state.completed_nodes.append(name)

        yield OrchestratorEvent(node="graph", event_type="complete")

    def get_graph(self) -> list[Edge]:
        """Return the edge list."""
        return list(self._edges)
