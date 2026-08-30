#!/usr/bin/env python3
"""PonyAgent benchmark script.

Measures:
- Message generation latency
- Memory operations (read/write)
- Sandbox execution speed
- Agent initialization
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def benchmark_memory_operations():
    """Test memory layer performance."""
    from ponyagent.memory.short_term import ShortTermMemory
    from ponyagent.memory.lesson_pool import LessonPool
    from ponyagent.types.message import Message
    from ponyagent.types.lesson import Lesson

    results = {}

    # Short-term memory
    st = ShortTermMemory()
    start = time.perf_counter()
    for i in range(1000):
        st.add(Message(role="user", content=f"Message {i}"))
    elapsed = time.perf_counter() - start
    results["short_term_write_ms"] = round(elapsed / 1000 * 1000, 3)
    print(f"  Short-term write: {results['short_term_write_ms']} ms/op (1000 ops)")

    # Lesson pool
    lp = LessonPool(path="/tmp/ponyagent_benchmark_lessons.json")
    start = time.perf_counter()
    for i in range(100):
        lp.add(Lesson(id=str(i), task="test task", error="test error"))
    elapsed = time.perf_counter() - start
    results["lesson_pool_write_ms"] = round(elapsed / 100 * 1000, 3)
    print(f"  Lesson pool write: {results['lesson_pool_write_ms']} ms/op (100 ops)")

    return results


def benchmark_sandbox():
    """Test sandbox execution speed."""
    from ponyagent.capabilities.sandbox import CodeSandbox

    results = {}
    sandbox = CodeSandbox()

    # AST check
    code = "x = 1\ny = 2\nresult = x + y\nprint(result)"
    start = time.perf_counter()
    for _ in range(100):
        sandbox.check_ast(code)
    elapsed = time.perf_counter() - start
    results["sandbox_ast_check_ms"] = round(elapsed / 100 * 1000, 3)
    print(f"  Sandbox AST check: {results['sandbox_ast_check_ms']} ms/op (100 ops)")

    return results


def benchmark_agent_creation():
    """Test agent initialization speed."""
    from ponyagent.ponyagent import PonyAgent

    start = time.perf_counter()
    for _ in range(10):
        PonyAgent()
    elapsed = time.perf_counter() - start
    results = {"agent_create_ms": round(elapsed / 10 * 1000, 3)}
    print(f"  Agent creation: {results['agent_create_ms']} ms/op (10 ops)")

    return results


def benchmark_event_log():
    """Test event log performance."""
    from ponyagent.memory.event_log import EventLog

    el = EventLog(run_id="benchmark")
    start = time.perf_counter()
    for i in range(500):
        el.append("message", role="user", content=f"msg {i}")
    elapsed = time.perf_counter() - start
    results = {"event_log_append_ms": round(elapsed / 500 * 1000, 3)}
    print(f"  EventLog append: {results['event_log_append_ms']} ms/op (500 ops)")

    return results


async def run_benchmarks():
    """Run all benchmarks."""
    print("=== PonyAgent Benchmarks ===\n")

    print("[1/5] Memory operations...")
    memory_results = benchmark_memory_operations()

    print("[2/5] Sandbox execution...")
    sandbox_results = benchmark_sandbox()

    print("[3/5] Agent creation...")
    agent_results = benchmark_agent_creation()

    print("[4/5] Event log...")
    event_results = benchmark_event_log()

    print("[5/5] Full run (stub model)...")
    from ponyagent.ponyagent import PonyAgent
    from ponyagent.models.stub_adapter import StubLLMAdapter

    agent = PonyAgent(llm=StubLLMAdapter())
    start = time.perf_counter()
    try:
        await agent.arun("Hello, this is a benchmark test")
        elapsed = time.perf_counter() - start
        results = {"full_run_ms": round(elapsed * 1000, 3)}
        print(f"  Full run (stub): {results['full_run_ms']} ms")
    except Exception as e:
        elapsed = time.perf_counter() - start
        results = {"full_run_ms": round(elapsed * 1000, 3)}
        print(f"  Full run: {results['full_run_ms']} ms (error: {e})")

    # Summary
    all_results = {**memory_results, **sandbox_results, **agent_results, **event_results, **results}
    print("\n=== Summary ===")
    for name, value in sorted(all_results.items()):
        print(f"  {name}: {value} ms")

    return all_results


if __name__ == "__main__":
    asyncio.run(run_benchmarks())
