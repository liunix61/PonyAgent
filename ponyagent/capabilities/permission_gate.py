"""Permission gate - tool call permission control (fx inspired)."""

from __future__ import annotations

import logging
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk classification for tool calls."""

    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PermissionResult(BaseModel):
    """Result of a permission check."""

    allowed: bool
    reason: str
    risk: RiskLevel = RiskLevel.LOW


class PermissionGate:
    """Permission gate for tool invocations.

    Classifies tool calls by risk level:
    - safe: auto-approved (read-only operations)
    - low: auto-approved with logging
    - medium: requires session-level approval
    - high/critical: requires explicit user approval
    """

    def __init__(
        self,
        safe_tools: set[str] | None = None,
        low_tools: set[str] | None = None,
        auto_approve_low: bool = True,
    ) -> None:
        self.safe_tools = safe_tools or {"get", "list", "read", "search", "query"}
        self.low_tools = low_tools or {"create", "write", "update"}
        self.auto_approve_low = auto_approve_low
        self._session_approved: set[str] = set()
        self._history: list[PermissionResult] = []

    def classify(self, tool_name: str) -> RiskLevel:
        """Classify a tool by risk level."""
        name = tool_name.lower()
        if name in self.safe_tools:
            return RiskLevel.SAFE
        if name in self.low_tools:
            return RiskLevel.LOW
        if "delete" in name or "drop" in name or "remove" in name:
            return RiskLevel.HIGH
        if "exec" in name or "shell" in name or "system" in name:
            return RiskLevel.CRITICAL
        return RiskLevel.MEDIUM

    async def check(self, tool_name: str, **args: object) -> PermissionResult:
        """Check permission for a tool call.

        Args:
            tool_name: Name of the tool to invoke.
            **args: Tool arguments for context.

        Returns:
            PermissionResult indicating allow/deny with reason.
        """
        risk = self.classify(tool_name)

        if risk == RiskLevel.SAFE:
            result = PermissionResult(
                allowed=True,
                reason="auto_safe",
                risk=risk,
            )
        elif risk == RiskLevel.LOW:
            if self.auto_approve_low:
                result = PermissionResult(
                    allowed=True,
                    reason="auto_low",
                    risk=risk,
                )
            elif f"{tool_name}*" in self._session_approved:
                result = PermissionResult(
                    allowed=True,
                    reason="session_approved",
                    risk=risk,
                )
            else:
                result = PermissionResult(
                    allowed=False,
                    reason="needs_approval",
                    risk=risk,
                )
        else:
            result = PermissionResult(
                allowed=False,
                reason="requires_user_approval",
                risk=risk,
            )

        self._history.append(result)
        return result

    def approve_session(self, tool_name: str) -> None:
        """Approve a tool for the current session."""
        self._session_approved.add(f"{tool_name}*")

    @property
    def history(self) -> list[PermissionResult]:
        """Return permission check history."""
        return list(self._history)

    def clear(self) -> None:
        """Clear history and session approvals."""
        self._session_approved.clear()
        self._history.clear()
