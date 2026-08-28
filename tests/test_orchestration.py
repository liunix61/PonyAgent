"""Tests for the orchestration package."""

import pytest

from ponyagent.orchestration import (
    Blackboard,
    CrewOrchestrator,
    DAGPipelineOrchestrator,
    StateGraphOrchestrator,
    TurnManagerOrchestrator,
    get_orchestrator,
    list_orchestrators,
    register_orchestrator,
)
from ponyagent.types.orchestration import (
    Edge,
    OrchestratorState,
    Role,
)


class TestStateGraphOrchestrator:
    async def test_simple_graph(self) -> None:
        graph = StateGraphOrchestrator()
        graph.add_node("start", lambda s: s.set("step", "start"))
        graph.add_node("end", lambda s: s.set("step", "end"))
        graph.add_edge("start", "end")
        graph.set_entry_point("start")
        graph.set_end("end")

        state = OrchestratorState()
        await graph.arun(state)
        assert state.state["step"] == "end"
        assert "start" in state.completed_nodes
        assert "end" in state.completed_nodes

    async def test_multi_node(self) -> None:
        graph = StateGraphOrchestrator()
        graph.add_node("a", lambda s: s.set("a", 1))
        graph.add_node("b", lambda s: s.set("b", 2))
        graph.add_node("c", lambda s: s.set("c", 3))
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        graph.set_entry_point("a")
        graph.set_end("c")

        state = OrchestratorState()
        await graph.arun(state)
        assert state.state["a"] == 1
        assert state.state["b"] == 2
        assert state.state["c"] == 3

    async def test_no_entry_point_raises(self) -> None:
        graph = StateGraphOrchestrator()
        graph.add_node("a", lambda s: s)
        state = OrchestratorState()
        with pytest.raises(ValueError, match="No entry point"):
            await graph.arun(state)

    async def test_stream(self) -> None:
        graph = StateGraphOrchestrator()
        graph.add_node("a", lambda s: s.set("done", True))
        graph.set_entry_point("a")
        graph.set_end("a")

        state = OrchestratorState()
        events = []
        async for event in graph.astream(state):
            events.append(event)
        assert events[0].event_type == "start"
        assert events[-1].event_type == "complete"

    def test_get_graph(self) -> None:
        graph = StateGraphOrchestrator()
        graph.add_edge("a", "b")
        edges = graph.get_graph()
        assert len(edges) == 1
        assert edges[0].source == "a"
        assert edges[0].target == "b"


class TestCrewOrchestrator:
    async def test_sequential(self) -> None:
        roles = [
            Role(name="researcher", goal="Research topic"),
            Role(name="writer", goal="Write report"),
        ]
        crew = CrewOrchestrator(roles, process="sequential")
        state = OrchestratorState()
        await crew.arun(state)
        assert "researcher" in state.completed_nodes
        assert "writer" in state.completed_nodes
        assert len(state.messages) >= 2

    async def test_hierarchical(self) -> None:
        roles = [
            Role(name="manager", goal="Delegate"),
            Role(name="worker1", goal="Task 1"),
            Role(name="worker2", goal="Task 2"),
        ]
        crew = CrewOrchestrator(roles, process="hierarchical")
        state = OrchestratorState()
        await crew.arun(state)
        assert "manager" in state.completed_nodes
        assert "worker1" in state.completed_nodes
        assert "worker2" in state.completed_nodes

    async def test_unknown_process_raises(self) -> None:
        crew = CrewOrchestrator([Role(name="a", goal="g")], process="invalid")
        with pytest.raises(ValueError, match="Unknown process"):
            await crew.arun(OrchestratorState())


class TestTurnManagerOrchestrator:
    async def test_basic_turns(self) -> None:
        roles = [
            Role(name="a", goal="Goal A"),
            Role(name="b", goal="Goal B"),
        ]
        tm = TurnManagerOrchestrator(roles, max_turns=3)
        state = OrchestratorState()
        await tm.arun(state)
        assert state.get("total_turns") == 6  # 3 turns x 2 roles
        assert len(state.completed_nodes) == 6

    async def test_termination_max_turns(self) -> None:
        roles = [Role(name="a", goal="g")]
        tm = TurnManagerOrchestrator(roles, max_turns=2)
        state = OrchestratorState()
        await tm.arun(state)
        assert state.get("total_turns") == 2

    async def test_stream(self) -> None:
        roles = [Role(name="a", goal="g")]
        tm = TurnManagerOrchestrator(roles, max_turns=1)
        state = OrchestratorState()
        events = []
        async for e in tm.astream(state):
            events.append(e)
        assert events[0].event_type == "start"
        assert events[-1].event_type == "complete"


class TestDAGPipelineOrchestrator:
    def _make_dag(self) -> DAGPipelineOrchestrator:
        edges = [Edge(source="a", target="b"), Edge(source="b", target="c")]
        return DAGPipelineOrchestrator(["a", "b", "c"], edges)

    async def test_pipeline(self) -> None:
        dag = self._make_dag()
        state = OrchestratorState()
        await dag.arun(state)
        assert "a" in state.completed_nodes
        assert "b" in state.completed_nodes
        assert "c" in state.completed_nodes

    async def test_roundtable(self) -> None:
        dag = DAGPipelineOrchestrator(
            ["a", "b"],
            [],
            mode="roundtable",
        )
        state = OrchestratorState()
        await dag.arun(state)
        assert state.get("a_output") is not None

    async def test_parallel(self) -> None:
        dag = DAGPipelineOrchestrator(["a", "b"], [], mode="parallel")
        state = OrchestratorState()
        await dag.arun(state)
        assert "a" in state.completed_nodes

    async def test_debate(self) -> None:
        dag = DAGPipelineOrchestrator(["a", "b"], [], mode="debate")
        state = OrchestratorState()
        await dag.arun(state)
        assert state.get("a_position") is not None

    async def test_unknown_mode_raises(self) -> None:
        dag = DAGPipelineOrchestrator(["a"], [], mode="invalid")
        with pytest.raises(ValueError):
            await dag.arun(OrchestratorState())

    def test_get_graph(self) -> None:
        dag = self._make_dag()
        edges = dag.get_graph()
        assert len(edges) == 2


class TestBlackboard:
    def test_write_read(self) -> None:
        bb = Blackboard()
        bb.write("key", "value", writer="agent1")
        assert bb.read("key") == "value"

    def test_read_default(self) -> None:
        bb = Blackboard()
        assert bb.read("missing") is None
        assert bb.read("missing", "default") == "default"

    def test_keys(self) -> None:
        bb = Blackboard()
        bb.write("a", 1)
        bb.write("b", 2)
        keys = bb.keys()
        assert "a" in keys and "b" in keys

    def test_clear(self) -> None:
        bb = Blackboard()
        bb.write("a", 1)
        bb.clear()
        assert bb.read("a") is None

    def test_get_writer(self) -> None:
        bb = Blackboard()
        bb.write("a", 1, writer="agent1")
        assert bb.get_writer("a") == "agent1"
        assert bb.get_writer("missing") is None


class TestRegistry:
    def test_builtin_orchestrators(self) -> None:
        names = list_orchestrators()
        assert "graph" in names
        assert "crew" in names
        assert "turn" in names
        assert "dag_pipeline" in names

    def test_get_orchestrator(self) -> None:
        cls = get_orchestrator("graph")
        assert cls is StateGraphOrchestrator

    def test_get_unknown_raises(self) -> None:
        with pytest.raises(KeyError, match="not registered"):
            get_orchestrator("nonexistent")

    def test_register_custom(self) -> None:
        @register_orchestrator("custom_test")
        class CustomOrch:
            pass

        assert "custom_test" in list_orchestrators()
        assert get_orchestrator("custom_test") is CustomOrch
