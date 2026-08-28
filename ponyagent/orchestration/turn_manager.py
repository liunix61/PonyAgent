"""TurnManagerOrchestrator - conversation/debate mode (AutoGen-style).

Manages multi-turn conversations with turn-based speaking rights,
supporting debate and negotiation patterns.
"""

from __future__ import annotations

from ponyagent.types.orchestration import (
    OrchestratorEvent,
    OrchestratorState,
    Role,
)


class TurnManagerOrchestrator:
    """AutoGen-style turn-based conversation orchestrator.

    Agents take turns speaking. Each turn contributes to
    a shared message history. Supports round-robin and
    termination conditions.
    """

    def __init__(
        self,
        roles: list[Role],
        max_turns: int = 5,
        termination: str = "max_turns",
    ) -> None:
        self.roles = roles
        self.max_turns = max_turns
        self.termination = termination

    async def arun(self, state: OrchestratorState) -> OrchestratorState:
        """Run turn-based conversation."""
        total_turns = 0
        for turn in range(self.max_turns):
            for role in self.roles:
                total_turns += 1
                state.current_node = role.name
                state.add_message(
                    "assistant",
                    f"[{role.name}] Turn {turn + 1}: Working on {role.goal}",
                )
                state.set(f"{role.name}_last_turn", turn + 1)
                state.completed_nodes.append(role.name)

            # Check termination
            if self.termination == "all_agree" and self._check_agreement(state):
                break

        state.current_node = None
        state.set("total_turns", total_turns)
        return state

    def _check_agreement(self, state: OrchestratorState) -> bool:
        """Check if all roles have reached agreement."""
        return state.get("agreement_reached", False)

    async def astream(self, state: OrchestratorState):
        """Stream turn events."""
        yield OrchestratorEvent(node="turn", event_type="start")

        for turn in range(self.max_turns):
            for role in self.roles:
                yield OrchestratorEvent(
                    node=role.name,
                    event_type="turn_start",
                    data={"turn": turn + 1},
                )
                state.add_message(
                    "assistant",
                    f"[{role.name}] Turn {turn + 1}: {role.goal}",
                )
                state.completed_nodes.append(role.name)
                yield OrchestratorEvent(
                    node=role.name,
                    event_type="turn_end",
                    data={"turn": turn + 1},
                )

            if self.termination == "all_agree" and self._check_agreement(state):
                break

        yield OrchestratorEvent(node="turn", event_type="complete")

    def get_graph(self) -> None:
        """Turn mode has no explicit DAG."""
        return None
