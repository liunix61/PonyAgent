"""Profile patches - user overlay layer (Cordis-style)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PatchFile:
    """Applies a YAML/JSON patch to a Profile."""

    @staticmethod
    def load(path: Path | str) -> dict[str, Any]:
        """Load a patch file (JSON only for now)."""
        p = Path(path)
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def apply(target: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
        """Deep-merge patch into target."""
        result = dict(target)
        for key, value in patch.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = PatchFile.apply(result[key], value)
            else:
                result[key] = value
        return result
