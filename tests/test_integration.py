"""Tests for config, plugin manager, models, and PonyAgent integration."""

import pytest

from ponyagent import PonyAgent
from ponyagent.config.profile import Bundle, Profile
from ponyagent.core.plugin_manager import PluginManager, SharedContext
from ponyagent.models.openai_adapter import OpenAIAdapter
from ponyagent.models.stub_adapter import StubLLMAdapter
from ponyagent.types.message import Message


class TestProfile:
    def test_single_bundle(self) -> None:
        p = Profile(name="base", bundles=[Bundle(name="core", plugins=["a", "b"])])
        assert p.resolve_plugins() == ["a", "b"]

    def test_multiple_bundles(self) -> None:
        p = Profile(
            name="full",
            bundles=[
                Bundle(name="core", plugins=["a"]),
                Bundle(name="extra", plugins=["b", "c"]),
            ],
        )
        assert p.resolve_plugins() == ["a", "b", "c"]

    def test_config_merge(self) -> None:
        p = Profile(
            name="cfg",
            bundles=[
                Bundle(name="a", config={"x": 1}),
                Bundle(name="b", config={"y": 2}),
            ],
        )
        cfg = p.resolve_config()
        assert cfg == {"x": 1, "y": 2}

    def test_patches_override(self) -> None:
        p = Profile(
            name="cfg",
            bundles=[Bundle(name="a", config={"x": 1, "y": 2})],
        )
        p.patch("x", 99)
        cfg = p.resolve_config()
        assert cfg["x"] == 99
        assert cfg["y"] == 2

    def test_add_bundle(self) -> None:
        p = Profile(name="p")
        p.add_bundle(Bundle(name="a", plugins=["x"]))
        p.add_bundle(Bundle(name="b", plugins=["y"]))
        assert p.resolve_plugins() == ["x", "y"]

    def test_to_dict(self) -> None:
        p = Profile(name="p", bundles=[Bundle(name="a", plugins=["x"])])
        d = p.to_dict()
        assert d["name"] == "p"
        assert d["bundles"][0]["plugins"] == ["x"]


class TestSharedContext:
    def test_register_and_get(self) -> None:
        ctx = SharedContext()
        ctx.register("plugin_a", "service1", "value1")
        assert ctx.get("service1") == "value1"

    async def test_rollback(self) -> None:
        ctx = SharedContext()
        ctx.register("plugin_a", "k", "v1")
        ctx.register("plugin_a", "k", "v2")
        assert ctx.get("k") == "v2"
        await ctx.rollback("plugin_a")
        # After rollback, k should be reverted
        assert ctx.get("k") is None

    def test_plugins_list(self) -> None:
        ctx = SharedContext()
        ctx.register("a", "x", 1)
        ctx.register("b", "y", 2)
        plugins = ctx.plugins()
        assert "a" in plugins
        assert "b" in plugins

    def test_clear(self) -> None:
        ctx = SharedContext()
        ctx.register("a", "x", 1)
        ctx.clear()
        assert ctx.get("x") is None


class TestPluginManager:
    def test_register_plugin(self) -> None:
        pm = PluginManager()
        pm.ctx  # ensure ctx exists
        assert pm.list_plugins() == []

    async def test_activate_unknown_raises(self) -> None:
        pm = PluginManager()
        with pytest.raises(KeyError):
            await pm.activate("nonexistent")


class TestStubLLMAdapter:
    async def test_returns_canned_responses(self) -> None:
        responses = [Message(role="assistant", content="hello"), Message(role="assistant", content="world")]
        adapter = StubLLMAdapter(responses)
        r1 = await adapter.complete([])
        r2 = await adapter.complete([])
        assert r1.content == "hello"
        assert r2.content == "world"

    async def test_echoes_user(self) -> None:
        adapter = StubLLMAdapter()
        msg = await adapter.complete([Message(role="user", content="hi there")])
        assert "[stub]" in msg.content
        assert "hi there" in msg.content


class TestOpenAIAdapter:
    def test_model_name(self) -> None:
        adapter = OpenAIAdapter(model="gpt-4o-mini")
        assert adapter.model_name() == "gpt-4o-mini"

    async def test_no_key_raises(self) -> None:
        adapter = OpenAIAdapter(api_key="")
        with pytest.raises(ValueError, match="API key"):
            await adapter.complete([])


class TestPonyAgent:
    async def test_arun(self) -> None:
        llm = StubLLMAdapter([Message(role="assistant", content="Hello!")])
        agent = PonyAgent(model="test", llm=llm)
        ctx = await agent.arun("say hello")
        assert "Hello!" in ctx.state.get("final_content", "")

    async def test_info(self) -> None:
        agent = PonyAgent(model="gpt-4o", orchestrator="crew")
        info = agent.info()
        assert info["model"] == "gpt-4o"
        assert info["orchestrator"] == "crew"

    async def test_agent_property(self) -> None:
        llm = StubLLMAdapter()
        agent = PonyAgent(llm=llm)
        assert agent.agent is None  # not created until arun
        await agent.arun("test")
        assert agent.agent is not None

    async def test_max_steps(self) -> None:
        # Stub with tool call that never terminates
        from ponyagent.types.message import Message as Msg
        import json

        responses = [
            Msg(
                role="assistant",
                content="thinking",
                tool_calls=[{"id": f"c{i}", "name": "noop", "arguments": {}}],
            )
            for i in range(20)
        ]
        llm = StubLLMAdapter(responses)
        agent = PonyAgent(llm=llm, max_steps=3)
        ctx = await agent.arun("infinite")
        assert ctx.step == 3
