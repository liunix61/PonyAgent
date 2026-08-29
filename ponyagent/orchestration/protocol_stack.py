"""Protocol stack orchestrator (UniAgents/OPCOS-style)."""

from __future__ import annotations

from typing import Any, AsyncIterator, Callable

from ponyagent.types.orchestration import (
    OrchestratorEvent,
    OrchestratorState,
    OrchestrationMode,
)


class ProtocolStackOrchestrator:
    """Protocol-stack orchestration (A2A/MCP/ARD/OKF/ACP).

    Each protocol is a pipeline of handlers (interceptors).
    Messages pass through each handler in sequence.
    """

    mode: OrchestrationMode = "protocol_stack"

    def __init__(self, protocols: dict[str, list[Callable]] | None = None) -> None:
        self._protocols: dict[str, list[Callable]] = protocols or {}
        self._history: list[OrchestratorEvent] = []

    def register_protocol(self, name: str, handlers: list[Callable]) -> None:
        self._protocols[name] = handlers

    async def arun(self, state: OrchestratorState) -> OrchestratorState:
        """Run a protocol pipeline."""
        for proto_name, handlers in self._protocols.items():
            state = self._run_protocol(proto_name, handlers, state)
        return state

    def _run_protocol(
        self, name: str, handlers: list[Callable], state: OrchestratorState
    ) -> OrchestratorState:
        self._history.append(OrchestratorEvent(
            node=name, event_type="protocol_start", data={"handler_count": len(handlers)},
        ))
        for handler in handlers:
            try:
                result = handler(state)
                if hasattr(result, "__await__"):
                    import asyncio
                    result = asyncio.run(result)
                if isinstance(result, OrchestratorState):
                    state = result
            except Exception as e:
                self._history.append(OrchestratorEvent(
                    node=name, event_type="error", data={"error": str(e)},
                ))
        self._history.append(OrchestratorEvent(
            node=name, event_type="protocol_end", data={},
        ))
        return state

    async def astream(self, state: OrchestratorState) -> AsyncIterator[OrchestratorEvent]:
        final = await self.arun(state)
        for ev in self._history:
            yield ev
        yield OrchestratorEvent(node="", event_type="complete", data={"state_size": len(final.state)})

    def get_graph(self) -> dict[str, Any]:
        return {p: [h.__name__ for h in hs] for p, hs in self._protocols.items()}
