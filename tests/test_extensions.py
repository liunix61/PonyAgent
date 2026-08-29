"""Tests for the new types, memory layers, evolution backends, and adapters."""

import os
import tempfile

import pytest

from ponyagent.capabilities.tool_registry import ToolRegistry
from ponyagent.core.hooks import HookRegistry
from ponyagent.evolution.hermes_backend import HermesSkillBackend
from ponyagent.evolution.matrix_backend import MatrixCodeBackend
from ponyagent.memory.episodic import EpisodicMemory
from ponyagent.memory.lesson_pool import LessonPool
from ponyagent.memory.long_term import LongTermMemory
from ponyagent.memory.short_term import ShortTermMemory
from ponyagent.models.anthropic import AnthropicAdapter
from ponyagent.models.deepseek import DeepSeekAdapter
from ponyagent.models.litellm import LiteLLMAdapter
from ponyagent.orchestration.protocol_stack import ProtocolStackOrchestrator
from ponyagent.types.orchestration import OrchestratorState
from ponyagent.types.lesson import Lesson
from ponyagent.types.message import Message
from ponyagent.types.permission import PermissionResult
from ponyagent.types.response import AgentResponse, TokenUsage
from ponyagent.types.session import SessionEvent
from ponyagent.types.skill import Skill


class TestNewTypes:
    def test_token_usage(self) -> None:
        tu = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        assert tu.total_tokens == 15

    def test_agent_response(self) -> None:
        resp = AgentResponse(content="hi", usage=TokenUsage(total_tokens=1))
        assert resp.content == "hi"
        assert resp.finish_reason == "stop"

    def test_session_event(self) -> None:
        ev = SessionEvent(type="user/message", data={"content": "hello"})
        msg = ev.to_message()
        assert msg is not None
        assert msg.content == "hello"

    def test_session_event_non_message(self) -> None:
        ev = SessionEvent(type="turn/start", data={})
        assert ev.to_message() is None

    def test_skill_success_rate(self) -> None:
        s = Skill(id="s1", name="n", description="d", code="", success_count=3, failure_count=1)
        assert s.success_rate == 0.75

    def test_skill_zero_usage(self) -> None:
        s = Skill(id="s1", name="n", description="d", code="")
        assert s.success_rate == 1.0  # no usage yet — treat as 1.0

    def test_skill_failure_rate(self) -> None:
        s = Skill(id="s1", name="n", description="d", code="", success_count=0, failure_count=1)
        assert s.success_rate == 0.0

    def test_lesson(self) -> None:
        l = Lesson(id="l1", task="t", error="e")
        assert l.resolved is False

    def test_permission_result(self) -> None:
        pr = PermissionResult(allowed=True, reason="auto_safe", tool="x")
        assert pr.allowed


class TestShortTermMemory:
    def test_add_and_messages(self) -> None:
        st = ShortTermMemory(max_messages=5)
        for i in range(3):
            st.add(Message(role="user", content=f"m{i}"))
        assert st.size == 3
        assert len(st.messages) == 3

    def test_fifo_window(self) -> None:
        st = ShortTermMemory(max_messages=3)
        for i in range(5):
            st.add(Message(role="user", content=f"m{i}"))
        assert st.size == 3
        assert st.messages[0].content == "m2"

    def test_token_budget_eviction(self) -> None:
        st = ShortTermMemory(max_messages=5, max_tokens=20)
        for i in range(10):
            st.add(Message(role="user", content="x" * 100))
        # Each message ~25 tokens > 20 budget, so evict down to 1
        assert st.size == 1
        assert st.token_budget == 25

    def test_clear(self) -> None:
        st = ShortTermMemory()
        st.add(Message(role="user", content="hi"))
        st.clear()
        assert st.size == 0


class TestLongTermMemory:
    def test_add_and_count(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            lt = LongTermMemory(db_path=os.path.join(td, "test.sqlite"))
            import asyncio
            asyncio.run(lt.add("hello world", metadata={"src": "test"}))
            assert lt.count() == 1

    def test_search(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            lt = LongTermMemory(db_path=os.path.join(td, "test.sqlite"))
            import asyncio
            asyncio.run(lt.add("hello world", source="a"))
            results = asyncio.run(lt.search("hello"))
            assert len(results) == 1
            assert results[0]["content"] == "hello world"

    def test_delete(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            lt = LongTermMemory(db_path=os.path.join(td, "test.sqlite"))
            import asyncio
            mid = asyncio.run(lt.add("delete me"))
            assert asyncio.run(lt.delete(mid)) is True
            assert lt.count() == 0


class TestEpisodicMemory:
    def test_add_and_count(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ep = EpisodicMemory(path=os.path.join(td, "ep.json"))
            ep.add("first episode", tags=["test"])
            ep.add("second episode", tags=["test"])
            assert ep.count() == 2

    def test_search(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ep = EpisodicMemory(path=os.path.join(td, "ep.json"))
            ep.add("hello world", tags=["greeting"])
            ep.add("foo bar", tags=["other"])
            results = ep.search("hello")
            assert len(results) == 1
            assert "hello" in results[0]["content"]

    def test_clear(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ep = EpisodicMemory(path=os.path.join(td, "ep.json"))
            ep.add("x")
            ep.clear()
            assert ep.count() == 0


class TestLessonPool:
    def test_add_and_search(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            pool = LessonPool(path=os.path.join(td, "lessons.json"))
            l = Lesson(id="l1", task="add two numbers", error="TypeError")
            pool.add(l)
            assert pool.count() == 1
            results = pool.search("add")
            assert len(results) == 1

    def test_clear(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            pool = LessonPool(path=os.path.join(td, "lessons.json"))
            pool.add(Lesson(id="l1", task="x", error="y"))
            pool.clear()
            assert pool.count() == 0


class TestToolRegistry:
    def test_register_fn_and_invoke(self) -> None:
        reg = ToolRegistry()
        reg.register_fn(lambda x: x * 2, name="double")
        import asyncio
        result = asyncio.run(reg.invoke("double", {"x": 21}))
        assert result.status == "success"
        assert result.output == "42"

    def test_not_found(self) -> None:
        reg = ToolRegistry()
        import asyncio
        result = asyncio.run(reg.invoke("nope", {}))
        assert result.status == "error"

    def test_list_tools(self) -> None:
        reg = ToolRegistry()
        reg.register_fn(lambda: "x", name="a")
        reg.register_fn(lambda: "y", name="b")
        assert len(reg.list_tools()) == 2


class TestProtocolStack:
    async def test_basic_pipeline(self) -> None:
        def upper(state):
            state.set("val", state.get("val", "").upper())
            return state

        def prefix(state):
            state.set("val", ">>" + state.get("val", ""))
            return state

        orch = ProtocolStackOrchestrator()
        orch.register_protocol("text", [upper, prefix])
        state = OrchestratorState(state={"val": "hello"})
        final = await orch.arun(state)
        assert final.get("val") == ">>HELLO"

    async def test_stream(self) -> None:
        orch = ProtocolStackOrchestrator()
        orch.register_protocol("p", [lambda s: s])
        events = [ev async for ev in orch.astream(OrchestratorState())]
        assert any(ev.event_type == "complete" for ev in events)


class TestHooks:
    async def test_on_and_trigger(self) -> None:
        reg = HookRegistry()
        received: list[str] = []

        async def cb(data):
            received.append(data["x"])

        reg.on("test", cb)
        await reg.trigger("test", {"x": "hello"})
        assert received == ["hello"]

    def test_events_list(self) -> None:
        reg = HookRegistry()

        async def cb(data):
            pass

        reg.on("a", cb)
        reg.on("b", cb)
        assert "a" in reg.events()


class TestAdapters:
    def test_openai_adapter(self) -> None:
        from ponyagent.capabilities.adapters import OpenAIToolAdapter

        spec = OpenAIToolAdapter.convert({
            "type": "function",
            "function": {"name": "add", "description": "add two", "parameters": {"type": "object"}},
        })
        assert spec.name == "add"

    def test_mcp_adapter(self) -> None:
        from ponyagent.capabilities.adapters import MCPToolAdapter

        spec = MCPToolAdapter.convert({"name": "search", "description": "d", "inputSchema": {}})
        assert spec.name == "search"


class TestModelAdapters:
    async def test_anthropic_no_key(self) -> None:
        a = AnthropicAdapter(api_key="")
        with pytest.raises(ValueError):
            await a.complete([])

    async def test_litellm_no_key(self) -> None:
        a = LiteLLMAdapter(api_key="")
        with pytest.raises(ValueError):
            await a.complete([])

    def test_deepseek_model_name(self) -> None:
        d = DeepSeekAdapter(api_key="x")
        assert d.model_name() == "deepseek-chat"


class TestEvolutionBackends:
    async def test_hermes_learn_success(self, tmp_path) -> None:
        backend = HermesSkillBackend(skills_dir=tmp_path / "skills")
        skill = await backend.learn("add two numbers", "def add(a,b): return a+b", success=True)
        assert skill is not None
        skills = await backend.search("add")
        assert len(skills) == 1

    async def test_hermes_learn_failure(self, tmp_path) -> None:
        backend = HermesSkillBackend(skills_dir=tmp_path / "skills")
        skill = await backend.learn("task", "err", success=False)
        assert skill is None

    async def test_matrix_safe_code(self) -> None:
        backend = MatrixCodeBackend()
        skill = await backend.learn("compute", "x = 42", success=True)
        assert skill is not None

    async def test_matrix_dangerous_code(self) -> None:
        backend = MatrixCodeBackend()
        skill = await backend.learn("hack", "import os; os.system('ls')", success=True)
        assert skill is None
