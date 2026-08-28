"""Tests for capabilities and evolution packages."""

import pytest

from ponyagent.capabilities.code_generator import CodeGenerator
from ponyagent.capabilities.permission_gate import PermissionGate, RiskLevel
from ponyagent.capabilities.sandbox import CodeSandbox
from ponyagent.capabilities.skill_graph import SkillGraph, Skill
from ponyagent.evolution.lesson_backend import LessonBackend, Lesson
from ponyagent.evolution.replay_backend import ReplayBackend
from ponyagent.types.context import RunContext


class TestCodeSandbox:
    async def test_safe_code(self) -> None:
        sandbox = CodeSandbox()
        result = await sandbox.execute("x = 2 + 3\nprint(x)")
        assert result.success is True
        assert result.output == "5"

    async def test_import_blocked(self) -> None:
        sandbox = CodeSandbox()
        result = await sandbox.execute("import os")
        assert result.success is False
        assert "Import" in result.error

    async def test_exec_blocked(self) -> None:
        sandbox = CodeSandbox()
        result = await sandbox.execute("exec('print(1)')")
        assert result.success is False

    async def test_syntax_error(self) -> None:
        sandbox = CodeSandbox()
        result = await sandbox.execute("def broken(:")
        assert result.success is False
        assert "Syntax" in result.error

    async def test_execution_error(self) -> None:
        sandbox = CodeSandbox()
        result = await sandbox.execute("x = 1 / 0")
        assert result.success is False
        assert result.error and "zero" in result.error.lower()

    async def test_history(self) -> None:
        sandbox = CodeSandbox()
        await sandbox.execute("print(1)")
        await sandbox.execute("import os")
        assert len(sandbox.history) == 2
        sandbox.clear()
        assert len(sandbox.history) == 0

    def test_check_ast_safe(self) -> None:
        sandbox = CodeSandbox()
        safe, err = sandbox.check_ast("x = 42")
        assert safe is True
        assert err is None

    def test_check_ast_dangerous(self) -> None:
        sandbox = CodeSandbox()
        safe, err = sandbox.check_ast("import os")
        assert safe is False
        assert err is not None


class TestPermissionGate:
    async def test_safe_tool(self) -> None:
        gate = PermissionGate()
        result = await gate.check("get")
        assert result.allowed is True
        assert result.risk == RiskLevel.SAFE

    async def test_unknown_tool_needs_approval(self) -> None:
        gate = PermissionGate()
        result = await gate.check("delete_file")
        assert result.allowed is False
        assert result.risk == RiskLevel.HIGH

    async def test_session_approval(self) -> None:
        gate = PermissionGate(auto_approve_low=False)
        result1 = await gate.check("create")
        assert result1.allowed is False
        gate.approve_session("create")
        result2 = await gate.check("create")
        assert result2.allowed is True
        assert "session" in result2.reason

    async def test_history(self) -> None:
        gate = PermissionGate()
        await gate.check("get")
        await gate.check("delete")
        assert len(gate.history) == 2
        gate.clear()
        assert len(gate.history) == 0

    def test_classify_safe(self) -> None:
        gate = PermissionGate()
        assert gate.classify("get") == RiskLevel.SAFE
        assert gate.classify("read") == RiskLevel.SAFE

    def test_classify_high(self) -> None:
        gate = PermissionGate()
        assert gate.classify("delete") == RiskLevel.HIGH

    def test_classify_critical(self) -> None:
        gate = PermissionGate()
        assert gate.classify("exec") == RiskLevel.CRITICAL


class TestSkillGraph:
    async def test_learn_success(self) -> None:
        sg = SkillGraph()
        skill = await sg.learn("add numbers", 5, success=True, code="return a+b")
        assert skill is not None
        assert sg.skill_count == 1

    async def test_learn_failure(self) -> None:
        sg = SkillGraph()
        skill = await sg.learn("add numbers", "error", success=False)
        assert skill is None
        assert sg.lesson_count == 1

    async def test_search(self) -> None:
        sg = SkillGraph()
        await sg.learn("add two numbers", "ok", True, code="a+b")
        await sg.learn("multiply numbers", "ok", True, code="a*b")
        results = await sg.search("add")
        assert len(results) == 1
        assert "add" in results[0].name

    async def test_install(self) -> None:
        sg = SkillGraph()
        skill = Skill(name="custom", description="test")
        assert await sg.install(skill) is True
        assert sg.skill_count == 1

    async def test_record_usage(self) -> None:
        sg = SkillGraph()
        skill = await sg.learn("test", "ok", True)
        sg.record_usage(skill.id, success=True)
        sg.record_usage(skill.id, success=False)
        assert skill.usage_count == 2
        assert skill.success_rate == 0.5

    async def test_get_lessons(self) -> None:
        sg = SkillGraph()
        await sg.learn("task1", "err1", False)
        await sg.learn("task2", "err2", False)
        lessons = await sg.get_lessons()
        assert len(lessons) == 2
        filtered = await sg.get_lessons("task1")
        assert len(filtered) == 1

    def test_clear(self) -> None:
        sg = SkillGraph()
        sg._skills["a"] = Skill(name="a", description="a")
        sg._lessons.append({"task": "x"})
        sg.clear()
        assert sg.skill_count == 0
        assert sg.lesson_count == 0


class TestCodeGenerator:
    async def test_generate(self) -> None:
        gen = CodeGenerator()
        code = await gen.generate("add two numbers")
        assert "def solution" in code
        assert "add two numbers" in code

    async def test_validate_safe(self) -> None:
        gen = CodeGenerator()
        result = await gen.validate("print(42)")
        assert result.success is True

    async def test_validate_dangerous(self) -> None:
        gen = CodeGenerator()
        result = await gen.validate("import os")
        assert result.success is False

    async def test_generate_and_validate(self) -> None:
        gen = CodeGenerator()
        code, result = await gen.generate_and_validate("test")
        assert isinstance(code, str)
        assert result.success is True


class TestLessonBackend:
    def test_record_and_search(self) -> None:
        lb = LessonBackend()
        lb.record("task1", "division by zero")
        lb.record("task2", "file not found")
        results = lb.search("division")
        assert len(results) == 1
        assert results[0].task == "task1"

    def test_get_recent(self) -> None:
        lb = LessonBackend()
        lb.record("a", "e1")
        lb.record("b", "e2")
        lb.record("c", "e3")
        recent = lb.get_recent(limit=2)
        assert len(recent) == 2

    def test_count_and_clear(self) -> None:
        lb = LessonBackend()
        lb.record("a", "e1")
        assert lb.count == 1
        lb.clear()
        assert lb.count == 0


class TestReplayBackend:
    def test_record_and_search(self) -> None:
        rb = ReplayBackend()
        ctx = RunContext(agent_id="a", state={"goal": "add numbers"})
        rb.record(ctx, "success", score=0.9)
        results = rb.search("add")
        assert len(results) == 1
        assert results[0].score == 0.9

    def test_success_rate(self) -> None:
        rb = ReplayBackend()
        rb.record(RunContext(agent_id="a"), "success")
        rb.record(RunContext(agent_id="a"), "failure")
        rb.record(RunContext(agent_id="a"), "success")
        assert rb.success_rate == pytest.approx(0.667, abs=0.01)

    def test_get_by_outcome(self) -> None:
        rb = ReplayBackend()
        rb.record(RunContext(agent_id="a"), "success")
        rb.record(RunContext(agent_id="a"), "failure")
        assert len(rb.get_by_outcome("success")) == 1
        assert len(rb.get_by_outcome("failure")) == 1

    def test_count_and_clear(self) -> None:
        rb = ReplayBackend()
        rb.record(RunContext(agent_id="a"), "success")
        assert rb.count == 1
        rb.clear()
        assert rb.count == 0
