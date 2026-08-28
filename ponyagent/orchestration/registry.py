"""Orchestrator registry - central lookup for all orchestration modes."""

from __future__ import annotations

from ponyagent.types.orchestration import OrchestratorProtocol

_ORCHESTRATORS: dict[str, type] = {}


def register_orchestrator(name: str) -> callable:
    """Decorator to register an orchestrator class."""

    def decorator(cls: type) -> type:
        _ORCHESTRATORS[name] = cls
        return cls

    return decorator


def get_orchestrator(name: str) -> type:
    """Retrieve a registered orchestrator class by name."""
    if name not in _ORCHESTRATORS:
        available = ", ".join(sorted(_ORCHESTRATORS.keys()))
        raise KeyError(f"Orchestrator '{name}' not registered. Available: {available}")
    return _ORCHESTRATORS[name]


def list_orchestrators() -> list[str]:
    """List all registered orchestrator names."""
    return sorted(_ORCHESTRATORS.keys())
