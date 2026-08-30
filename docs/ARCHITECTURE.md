# PonyAgent Architecture

PonyAgent is a lightweight, type-safe, self-evolving multi-agent operating system.

## 7-Layer Architecture

```
Layer 7: Interface     → CLI, FastAPI Server
Layer 6: Evolution     → 5 backends (Hermes, Matrix, Memory, Replay, Lesson)
Layer 5: Capabilities  → Sandbox, PermissionGate, SkillGraph, CodeGenerator
Layer 4: Orchestration → 5 orchestrators (Graph, Crew, TurnManager, DAG, Protocol)
Layer 3: Core          → ReAct Agent, PluginManager, Hooks, Config
Layer 2: Memory        → EventLog, StateSerializer, Short/Long/Episodic/Lesson
Layer 1: Types         → Pydantic v2 models (all types)
```

## Design Principles

1. **Type-safe**: Pydantic v2 for all data models
2. **Log-as-truth**: EventLog is the source of truth for run state
3. **Checkpoint/resume**: StateSerializer enables interrupt/resume
4. **Plugin-first**: PluginManager supports reversible registration
5. **Self-evolving**: 5 evolution backends learn from execution history

## Key Modules

| Layer | Module | Description |
|-------|--------|-------------|
| types | context, message, tool, orchestration | Data models |
| memory | event_log, state_serializer, short_term, long_term | State management |
| core | agent (ReAct), plugin_manager, hooks, config | Agent runtime |
| orchestration | graph, crew, turn_manager, dag_pipeline, protocol_stack | Coordination |
| capabilities | sandbox, permission_gate, skill_graph, code_generator | Execution safety |
| evolution | hermes_backend, matrix_backend, memory_backend, lesson_backend, replay_backend | Learning |
| models | openai, anthropic, deepseek, litellm, stub | LLM providers |
| interface | cli, server | User-facing |

## Verdict Pipeline

```
Static Analysis → Unit Tests → Sandbox Execution → Merge
     ↓                ↓              ↓
  ruff/lint      pytest          AST-based
                                safe execution
```

## Permission Levels

| Level | Behavior |
|-------|----------|
| auto_safe | No permission check (read-only, safe ops) |
| session_approved | Approved within session scope |
| user_confirm | Requires explicit user confirmation |
