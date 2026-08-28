"""Profile/Bundle configuration - composable plugin stacks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Bundle:
    """A distributable bundle of plugins with config."""

    name: str
    plugins: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class Profile:
    """Ordered stack of bundles forming a complete configuration."""

    name: str
    bundles: list[Bundle] = field(default_factory=list)
    patches: dict[str, Any] = field(default_factory=dict)

    def resolve_plugins(self) -> list[str]:
        """Resolve final plugin list from bundles in order."""
        plugins: list[str] = []
        for bundle in self.bundles:
            plugins.extend(bundle.plugins)
        return plugins

    def resolve_config(self) -> dict[str, Any]:
        """Merge all bundle configs with patches applied last."""
        merged: dict[str, Any] = {}
        for bundle in self.bundles:
            merged.update(bundle.config)
        merged.update(self.patches)
        return merged

    def add_bundle(self, bundle: Bundle) -> None:
        """Append a bundle to the profile."""
        self.bundles.append(bundle)

    def patch(self, key: str, value: Any) -> None:
        """Apply a user override."""
        self.patches[key] = value

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "bundles": [
                {"name": b.name, "plugins": b.plugins, "config": b.config}
                for b in self.bundles
            ],
            "patches": self.patches,
        }
