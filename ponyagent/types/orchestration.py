"""Orchestration types and protocol definitions."""

from __future__ import annotations

from typing import Any, Literal, Protocol, AsyncIterator

from pydantic import BaseModel, Field

OrchestrationMode = Literal[
    "graph",
    "crew",
    "turn",
    "protocol_stack",
    "dag_pipeline",
    "hybrid",
]


class OrchestratorState(BaseModel):
    """State container passed between orchestration nodes."""

    state: dict[str, Any] = Field(default_factory=dict)
    messages: list[dict[str, Any]] = Field(default_factory=list)
    current_node: str | None = None
    completed_nodes: list[str] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.state[key] = value


class OrchestratorEvent(BaseModel):
    """Event emitted during orchestration execution."""

    node: str
    event_type: str
    data: dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    """Directed edge in a graph or DAG."""

    source: str
    target: str
    condition: str | None = None


class Node(BaseModel):
    """A node in a graph or DAG."""

    name: str
    fn: Any = None  # Callable
    metadata: dict[str, Any] = Field(default_factory=dict)


class Role(BaseModel):
    """A role in a crew orchestration."""

    name: str
    goal: str
    backstory: str = ""
    tools: list[str] = Field(default_factory=list)
    llm: str = ""


class OrchestratorProtocol(Protocol):
    """Unified interface for all orchestrators.

    All orchestration modes implement this protocol:
    - graph: StateGraph (LangGraph-style)
    - crew: CrewOrchestrator (CrewAI-style)
    - turn: TurnManagerOrchestrator (AutoGen-style)
    - protocol_stack: ProtocolStackOrchestrator
    - dag_pipeline: DAGPipelineOrchestrator (MATRIX-style)
    """

    async def arun(self, state: OrchestratorState) -> OrchestratorState:
        """Execute the orchestration."""
        ...

    async def astream(
        self, state: OrchestratorState
    ) -> AsyncIterator[OrchestratorEvent]:
        """Stream orchestration events."""
        ...

    def get_graph(self) -> list[Edge] | None:
        """Return DAG structure if applicable."""
        ...
