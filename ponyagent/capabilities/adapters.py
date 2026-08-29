"""Tool adapters - LangChain/OpenAI/MCP compatibility."""

from __future__ import annotations

from typing import Any, Callable

from ponyagent.capabilities.tool_registry import ToolRegistry
from ponyagent.types.tool import ToolSpec


class LangChainAdapter:
    """Adapt LangChain tools to PonyAgent ToolSpec."""

    @staticmethod
    def convert(tool: Any) -> ToolSpec:
        """Convert a LangChain tool to PonyAgent ToolSpec."""
        try:
            return ToolSpec(
                name=getattr(tool, "name", "unknown"),
                description=getattr(tool, "description", ""),
                parameters=getattr(tool, "args_schema", {}) or {},
            )
        except Exception:
            return ToolSpec(name="unknown", description="", parameters={})


class OpenAIToolAdapter:
    """Convert OpenAI function-calling tools to PonyAgent ToolSpec."""

    @staticmethod
    def convert(tool: dict[str, Any]) -> ToolSpec:
        fn = tool.get("function", {})
        return ToolSpec(
            name=fn.get("name", "unknown"),
            description=fn.get("description", ""),
            parameters=fn.get("parameters", {}),
        )


class MCPToolAdapter:
    """Convert MCP tools to PonyAgent ToolSpec."""

    @staticmethod
    def convert(tool: dict[str, Any]) -> ToolSpec:
        return ToolSpec(
            name=tool.get("name", "unknown"),
            description=tool.get("description", ""),
            parameters=tool.get("inputSchema", {}),
        )


def adapt_all(
    registry: ToolRegistry,
    langchain_tools: list[Any] | None = None,
    openai_tools: list[dict] | None = None,
    mcp_tools: list[dict] | None = None,
) -> int:
    """Adapt tools from all frameworks into a registry. Returns count."""
    count = 0
    for t in langchain_tools or []:
        registry.register(LangChainAdapter.convert(t))
        count += 1
    for t in openai_tools or []:
        registry.register(OpenAIToolAdapter.convert(t))
        count += 1
    for t in mcp_tools or []:
        registry.register(MCPToolAdapter.convert(t))
        count += 1
    return count
