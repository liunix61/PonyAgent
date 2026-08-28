"""Tests for PonyAgent types."""

from ponyagent.types.context import RunContext
from ponyagent.types.message import Message, MessageRole
from ponyagent.types.tool import ToolCall, ToolResult, ToolSpec


class TestRunContext:
    def test_create_minimal(self) -> None:
        ctx = RunContext(agent_id="test-agent")
        assert ctx.run_id
        assert ctx.agent_id == "test-agent"
        assert ctx.step == 0
        assert ctx.state == {}
        assert ctx.metadata == {}
        assert ctx.parent_run_id is None

    def test_advance(self) -> None:
        ctx = RunContext(agent_id="test-agent")
        ctx.advance()
        assert ctx.step == 1
        ctx.advance()
        ctx.advance()
        assert ctx.step == 3

    def test_with_parent(self) -> None:
        ctx = RunContext(agent_id="child", parent_run_id="parent-123")
        assert ctx.parent_run_id == "parent-123"

    def test_metadata_and_state(self) -> None:
        ctx = RunContext(
            agent_id="a",
            metadata={"k": "v"},
            state={"x": 1},
        )
        assert ctx.metadata == {"k": "v"}
        assert ctx.state == {"x": 1}


class TestMessage:
    def test_basic_message(self) -> None:
        msg = Message(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"
        assert msg.tool_calls is None

    def test_all_roles(self) -> None:
        for role in ["system", "user", "assistant", "tool"]:
            msg = Message(role=role, content="x")
            assert msg.role == role

    def test_with_tool_calls(self) -> None:
        msg = Message(
            role="assistant",
            content="calling tool",
            tool_calls=[{"id": "c1", "name": "add", "arguments": {"a": 1}}],
        )
        assert len(msg.tool_calls) == 1


class TestToolSpec:
    def test_invoke(self) -> None:
        spec = ToolSpec(name="add", description="add", fn=lambda a, b: a + b)
        assert spec.invoke(a=2, b=3) == 5

    def test_no_fn_raises(self) -> None:
        spec = ToolSpec(name="x", description="x")
        try:
            spec.invoke()
            assert False, "should have raised"
        except ValueError:
            pass


class TestToolResult:
    def test_success(self) -> None:
        r = ToolResult(tool_call_id="c1", name="add", output="5")
        assert r.status == "success"

    def test_error(self) -> None:
        r = ToolResult(tool_call_id="c1", name="add", status="error", error="bad")
        assert r.status == "error"
