"""Hooks system - lifecycle callbacks (Cordis-inspired)."""

from __future__ import annotations

from typing import Any, Callable, Awaitable

HookCallback = Callable[[dict[str, Any]], Awaitable[None]]


class HookRegistry:
    """Register and trigger lifecycle hooks."""

    def __init__(self) -> None:
        self._hooks: dict[str, list[HookCallback]] = {}

    def on(self, event: str, callback: HookCallback) -> None:
        self._hooks.setdefault(event, []).append(callback)

    def off(self, event: str, callback: HookCallback) -> None:
        if event in self._hooks:
            self._hooks[event] = [cb for cb in self._hooks[event] if cb is not callback]

    async def trigger(self, event: str, data: dict[str, Any]) -> None:
        for cb in self._hooks.get(event, []):
            await cb(data)

    def events(self) -> list[str]:
        return list(self._hooks.keys())
