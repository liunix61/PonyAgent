# Changelog

All notable changes to PonyAgent are documented here.
Follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.
Adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-29

### Added
- **7-layer architecture**: types, memory, core, orchestration, capabilities, evolution, interface
- **Type-safe Pydantic v2 models**: RunContext, Message, ToolSpec, ToolCall, ToolResult
- **Memory layer**: EventLog, StateSerializer, ShortTermMemory, LongTermMemory (AIDB SQLite+FTS5), EpisodicMemory (AIMEM JSONL), LessonPool
- **Core agent**: ReAct loop with tool calling, permission gates
- **5 orchestrators**: Graph, Crew, TurnManager, DAGPipeline, ProtocolStack
- **Sandbox execution**: AST-based safe code execution
- **Permission gate**: auto_safe / session_approved / user_confirm modes
- **Skill graph**: Skill discovery, execution, and evolution
- **5 evolution backends**: Hermes, Matrix, Memory, Replay, Lesson
- **5 model adapters**: OpenAI, Anthropic, DeepSeek, LiteLLM, Stub
- **Plugin manager**: Reversible registration with rollback
- **CLI interface**: `ponyagent` CLI with chat, skill, serve commands
- **FastAPI server**: REST API on port 8000
- **E2E verification**: 10/10 end-to-end checks passed
- **150 unit tests**: 100% passing, covering all layers
- **Docker deployment**: Multi-stage Dockerfile with health check
- **GitHub Actions CI**: Multi-version testing + Docker build
- **Makefile**: Standard build, test, lint, docker targets

### Fixed
- Evolution backend `learn()` guard for backends without the method
- EventLog constructor requiring `run_id` parameter
- Orchestrator registry `get_orchestrator` signature
- ToolCall import path in types/response.py
- Skill success_rate calculation
- ShortTermMemory token budget eviction

## [0.0.1] - 2026-08-27

### Added
- Initial commit with project structure
- Phase 1: Core engine (types, memory, ReAct agent)
