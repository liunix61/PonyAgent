"""Tests for the core agent engine."""

import pytest

from ponyagent.core.agent import Agent, ToolRegistry, LLMClient
from ponyagent.types.message import Message
from ponyagent.types.tool import ToolSpec


class MockLLM:
    """Mock LLM that returns predefined responses."""

    def __init__(self, responses: list[Message]) -> None:
        self.responses = responses
        self.call_count = 0

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
    ) -> Message:
        idx = min(self.call_count, len(self.responses) - 1)
        self.call_count += 1
        return self.responses[idx]


class TestToolRegistry:
    def test_register_and_get(self) -> None:
        reg = ToolRegistry()
        spec = ToolSpec(name="add", description="add", fn=lambda a, b: a + b)
        reg.register(spec)
        assert reg.get("add") == spec
        assert "add" in reg
        assert len(reg) == 1

    def test_invoke_success(self) -> None:
        reg = ToolRegistry()
        reg.register(ToolSpec(name="add", description="add", fn=lambda a, b: a + b))
        from ponyagent.types.tool import ToolCall
        result = reg.invoke(ToolCall(id="c1", name="add", arguments={"a": 2, "b": 3}))
        assert result.status == "success"
        assert result.output == "5"

    def test_invoke_not_found(self) -> None:
        reg = ToolRegistry()
        from ponyagent.types.tool import ToolCall
        result = reg.invoke(ToolCall(id="c1", name="missing", arguments={}))
        assert result.status == "error"
        assert "not found" in result.error

    def test_invoke_tool_error(self) -> None:
        def bad_fn() -> int:
            raise ValueError("boom")

        reg = ToolRegistry()
        reg.register(ToolSpec(name="bad", description="bad", fn=bad_fn))
        from ponyagent.types.tool import ToolCall
        result = reg.invoke(ToolCall(id="c1", name="bad", arguments={}))
        assert result.status == "error"
        assert "boom" in result.error


class TestAgent:
    async def test_simple_no_tools(self) -> None:
        llm = MockLLM([Message(role="assistant", content="Hello! I can help.")])
        agent = Agent(agent_id="a1", llm=llm)
        ctx = await agent.run("greet me")
        assert ctx.state["final_content"] == "Hello! I can help."
        assert llm.call_count == 1

    async def test_with_tool_call(self) -> None:
        responses = [
            Message(
                role="assistant",
                content="calculating",
                tool_calls=[{"id": "c1", "name": "add", "arguments": {"a": 2, "b": 3}}],
            ),
            Message(role="assistant", content="The answer is 5."),
        ]
        llm = MockLLM(responses)
        reg = ToolRegistry()
        reg.register(ToolSpec(name="add", description="add", fn=lambda a, b: a + b))
        agent = Agent(agent_id="a1", llm=llm, tools=reg)
        ctx = await agent.run("add 2 and 3")
        assert "5" in ctx.state["final_content"]
        assert llm.call_count == 2

    async def test_max_steps(self) -> None:
        # LLM always returns a tool call, never terminates naturally
        responses = [
            Message(
                role="assistant",
                content="thinking",
                tool_calls=[{"id": f"c{i}", "name": "noop", "arguments": {}}],
            )
            for i in range(20)
        ]
        llm = MockLLM(responses)
        reg = ToolRegistry()
        reg.register(ToolSpec(name="noop", description="noop", fn=lambda: "ok"))
        agent = Agent(agent_id="a1", llm=llm, tools=reg, max_steps=3)
        ctx = await agent.run("infinite loop")
        assert ctx.step == 3
        assert llm.call_count == 3

    async def test_custom_system_prompt(self) -> None:
        llm = MockLLM([Message(role="assistant", content="hi")])
        agent = Agent(agent_id="a1", llm=llm, system_prompt="You are helpful.")
        await agent.run("hi")
        assert agent.system_prompt == "You are helpful."
