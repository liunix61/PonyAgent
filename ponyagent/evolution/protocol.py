"""Evolution protocol and registry."""

from __future__ import annotations

from typing import Any

from ponyagent.types.skill import Skill


class EvolutionProtocol:
    """Base class for evolution backends.

    Subclass to implement learn/search/install/get_lessons.
    """

    name: str = "base"

    async def learn(self, task: str, result: Any, success: bool) -> Skill | None:
        """Learn from a task execution."""
        return None

    async def search(self, query: str, top_k: int = 5) -> list[Skill]:
        """Search skills."""
        return []

    async def install(self, skill: Skill) -> bool:
        """Install a skill."""
        return True

    async def get_lessons(self, task: str) -> list[dict[str, Any]]:
        """Get lessons related to a task."""
        return []


class EvolutionRegistry:
    """Registry of evolution backends."""

    def __init__(self) -> None:
        self._backends: dict[str, type[EvolutionProtocol]] = {}

    def register(self, name: str, backend: type[EvolutionProtocol]) -> None:
        self._backends[name] = backend

    def get(self, name: str) -> type[EvolutionProtocol]:
        if name not in self._backends:
            raise KeyError(f"Evolution backend not registered: {name}")
        return self._backends[name]

    def list_backends(self) -> list[str]:
        return list(self._backends.keys())


# Global registry
_default_registry = EvolutionRegistry()


def register_evolution(name: str, backend: type[EvolutionProtocol]) -> None:
    _default_registry.register(name, backend)


def get_evolution(name: str) -> type[EvolutionProtocol]:
    return _default_registry.get(name)


def list_evolutions() -> list[str]:
    return _default_registry.list_backends()
