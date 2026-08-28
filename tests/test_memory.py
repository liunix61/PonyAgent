"""Tests for the memory package."""

import tempfile
from pathlib import Path

from ponyagent.memory.event_log import EventLog, LogEntry
from ponyagent.memory.state_serializer import StateSerializer
from ponyagent.types.context import RunContext


class TestEventLog:
    def test_append_and_entries(self) -> None:
        log = EventLog("run-1")
        log.append("start", goal="do thing")
        log.append("step", n=1)
        assert len(log) == 2
        assert len(log.entries()) == 2

    def test_last(self) -> None:
        log = EventLog("run-1")
        assert log.last() is None
        log.append("x", v=1)
        log.append("y", v=2)
        assert log.last().event_type == "y"

    def test_find(self) -> None:
        log = EventLog("run-1")
        log.append("step", n=1)
        log.append("other", v=2)
        log.append("step", n=3)
        steps = log.find("step")
        assert len(steps) == 2
        assert all(s.event_type == "step" for s in steps)

    def test_clear(self) -> None:
        log = EventLog("run-1")
        log.append("a")
        log.append("b")
        log.clear()
        assert len(log) == 0


class TestStateSerializer:
    def test_serialize_roundtrip(self) -> None:
        ctx = RunContext(agent_id="a", state={"x": 1}, metadata={"y": 2})
        data = StateSerializer.serialize(ctx)
        restored = StateSerializer.deserialize(data)
        assert restored.agent_id == "a"
        assert restored.state == {"x": 1}
        assert restored.metadata == {"y": 2}

    def test_save_and_load(self) -> None:
        ctx = RunContext(agent_id="a", state={"k": "v"})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            StateSerializer.save(ctx, path)
            assert path.exists()
            loaded = StateSerializer.load(path)
            assert loaded.state == {"k": "v"}
            assert loaded.agent_id == "a"

    def test_diff(self) -> None:
        before = RunContext(agent_id="a", state={"x": 1, "y": 2})
        after = RunContext(agent_id="a", state={"x": 10, "y": 2, "z": 3})
        diff = StateSerializer.diff(before, after)
        assert "x" in diff
        assert "z" in diff
        assert "y" not in diff  # unchanged
        assert diff["x"] == {"from": 1, "to": 10}
        assert diff["z"]["from"] is None
