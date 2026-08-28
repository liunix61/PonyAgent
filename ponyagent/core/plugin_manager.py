"""Plugin manager - reversible effect system (Cordis inspired)."""

from __future__ import annotations

from typing import Any, Callable, Protocol


class Effect:
    """A reversible registration effect."""

    def __init__(
        self,
        plugin: str,
        key: str,
        rollback: Callable[[], None],
    ) -> None:
        self.plugin = plugin
        self.key = key
        self._rollback = rollback

    def revert(self) -> None:
        """Revert this effect."""
        self._rollback()


class Context(Protocol):
    """Shared context for plugins."""

    def register(self, plugin: str, key: str, value: Any) -> Effect:
        ...

    def get(self, key: str, default: Any = None) -> Any:
        ...

    async def rollback(self, plugin: str) -> None:
        ...


class SharedContext:
    """Implementation of shared plugin context with rollback support."""

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}
        self._effects: dict[str, list[Effect]] = {}

    def register(self, plugin: str, key: str, value: Any) -> Effect:
        """Register a service with rollback capability."""
        old_value = self._services.get(key)

        def rollback() -> None:
            if old_value is not None:
                self._services[key] = old_value
            else:
                self._services.pop(key, None)

        effect = Effect(plugin, key, rollback)
        self._services[key] = value
        self._effects.setdefault(plugin, []).append(effect)
        return effect

    def get(self, key: str, default: Any = None) -> Any:
        """Get a registered service."""
        return self._services.get(key, default)

    async def rollback(self, plugin: str) -> None:
        """Roll back all effects for a plugin (in reverse order)."""
        for effect in reversed(self._effects.get(plugin, [])):
            effect.revert()
        self._effects.pop(plugin, None)

    def plugins(self) -> list[str]:
        """List all registered plugin names."""
        return list(self._effects.keys())

    def clear(self) -> None:
        """Clear all registrations."""
        self._services.clear()
        self._effects.clear()


class Plugin(Protocol):
    """Plugin interface - all components are plugins."""

    name: str
    version: str

    async def setup(self, ctx: SharedContext) -> None:
        """Install: register services, events, tools to ctx."""
        ...

    async def dispose(self, ctx: SharedContext) -> None:
        """Uninstall: rollback all registrations."""
        ...


class PluginManager:
    """Manages plugin lifecycle with reversible effects."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}
        self.ctx = SharedContext()

    def register(self, plugin: Plugin) -> None:
        """Register a plugin (not yet activated)."""
        self._plugins[plugin.name] = plugin

    async def activate(self, plugin_name: str) -> None:
        """Activate a registered plugin."""
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            raise KeyError(f"Plugin '{plugin_name}' not registered")
        await plugin.setup(self.ctx)

    async def deactivate(self, plugin_name: str) -> None:
        """Deactivate a plugin, rolling back its effects."""
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            raise KeyError(f"Plugin '{plugin_name}' not registered")
        await plugin.dispose(self.ctx)
        await self.ctx.rollback(plugin_name)

    async def activate_all(self) -> None:
        """Activate all registered plugins in order."""
        for name in self._plugins:
            await self.activate(name)

    async def deactivate_all(self) -> None:
        """Deactivate all plugins in reverse order."""
        for name in reversed(list(self._plugins)):
            try:
                await self.deactivate(name)
            except KeyError:
                pass

    def list_plugins(self) -> list[str]:
        """List all registered plugin names."""
        return list(self._plugins.keys())

    def is_active(self, plugin_name: str) -> bool:
        """Check if a plugin is active (has effects)."""
        return plugin_name in self.ctx.plugins()
