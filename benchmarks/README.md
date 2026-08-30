# PonyAgent Benchmarks

Performance benchmarks for the PonyAgent runtime.

## Running

```bash
python benchmarks/benchmark.py
```

Requires the Python venv from the project setup. The benchmark uses `StubLLMAdapter`
so no API keys or external network calls are needed.

## What It Measures

| Metric | Description |
|--------|-------------|
| `short_term_write_ms` | Cost of adding a message to `ShortTermMemory` |
| `lesson_pool_write_ms` | Cost of persisting a `Lesson` to disk |
| `sandbox_ast_check_ms` | Cost of AST safety check in `CodeSandbox` |
| `agent_create_ms` | Cost of initializing a `PonyAgent` instance |
| `event_log_append_ms` | Cost of appending an event to `EventLog` |
| `full_run_ms` | End-to-end `arun()` latency with stub model |
