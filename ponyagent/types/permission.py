"""Permission result type."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PermissionResult(BaseModel):
    """Result of a permission check."""

    allowed: bool
    reason: str
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
