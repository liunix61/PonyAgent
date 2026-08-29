"""Orchestrator registry - central lookup for all orchestration modes."""

from __future__ import annotations

from typing import Any, Callable

_ORCHESTRATORS: dict[str, type] = {}


def register_orchestrator(
    name: str | type | None = None,
    cls: type | None = None,
) -> Any:
    """Register an orchestrator class.

    Can be used as a plain function (register_orchestrator("name", Cls))
    or as a decorator (@register_orchestrator("name")).
    """
    if cls is not None and isinstance(name, str):
        _ORCHESTRATORS[name] = cls
        return cls
    if name is not None and isinstance(name, type):
        # Used as @register_orchestrator without parentheses — class is the name
        _ORCHESTRATORS[name.__name__.lower()] = name
        return name
    # Used as @register_orchestrator("name") — name is a string, no class
    def decorator(cls: type) -> type:
        _ORCHESTRATORS[name or cls.__name__.lower()] = cls
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
