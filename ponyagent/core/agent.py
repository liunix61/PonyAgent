"""Core Agent - the heart of PonyAgent.

Implements a minimal ReAct loop: think -> act -> observe -> repeat.
All actions are recorded in an EventLog for full traceability.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, Callable

from ponyagent.memory.event_log import EventLog
from ponyagent.memory.state_serializer import StateSerializer
from ponyagent.types.context import RunContext
from ponyagent.types.message import Message, MessageRole
from ponyagent.types.tool import ToolCall, ToolResult, ToolSpec

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    """Protocol for an LLM backend.

    Any object with a `complete` method that accepts messages and returns
    a string can be used as an LLM client.
    """

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
    ) -> Message:
        """Generate the next assistant message."""
        ...


class ToolRegistry:
    """Registry of available tools for an agent."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        """Register a tool specification."""
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec | None:
        """Retrieve a tool by name."""
        return self._tools.get(name)

    def list(self) -> list[ToolSpec]:
        """List all registered tools."""
        return list(self._tools.values())

    def invoke(self, call: ToolCall) -> ToolResult:
        """Invoke a tool by its ToolCall."""
        spec = self._tools.get(call.name)
        if spec is None:
            return ToolResult(
                tool_call_id=call.id,
                name=call.name,
                status="error",
                error=f"Tool '{call.name}' not found",
            )
        try:
            output = spec.invoke(**call.arguments)
            return ToolResult(
                tool_call_id=call.id,
                name=call.name,
                status="success",
                output=str(output),
            )
        except Exception as e:
            return ToolResult(
                tool_call_id=call.id,
                name=call.name,
                status="error",
                error=str(e),
            )

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools


class Agent:
    """A single autonomous agent with a ReAct loop.

    The agent:
    1. Receives a goal
    2. Calls the LLM to decide next actions
    3. Executes tools if requested
    4. Logs every step in an EventLog
    5. Stops when no more tool calls or max steps reached
    """

    def __init__(
        self,
        agent_id: str,
        llm: LLMClient,
        tools: ToolRegistry | None = None,
        max_steps: int = 10,
        system_prompt: str | None = None,
    ) -> None:
        self.agent_id = agent_id
        self.llm = llm
        self.tools = tools or ToolRegistry()
        self.max_steps = max_steps
        self.system_prompt = system_prompt or (
            "You are PonyAgent, a helpful autonomous agent."
        )

    async def run(self, goal: str, **ctx_kwargs: Any) -> RunContext:
        """Execute the ReAct loop for a given goal.

        Args:
            goal: The task the agent should accomplish.
            ctx_kwargs: Additional RunContext fields.

        Returns:
            The final RunContext with accumulated state.
        """
        ctx = RunContext(agent_id=self.agent_id, **ctx_kwargs)
        ctx.state["goal"] = goal
        log = EventLog(ctx.run_id)

        messages: list[Message] = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=goal),
        ]

        log.append("run_start", goal=goal)

        final_content = ""
        for step in range(1, self.max_steps + 1):
            ctx.advance()
            logger.debug("Step %d for %s", step, ctx.run_id)

            response = await self.llm.complete(messages, tools=self.tools.list())
            messages.append(response)
            final_content = response.content

            log.append("llm_response", step=ctx.step, content=final_content)

            if not response.tool_calls:
                log.append("run_complete", final_content=final_content)
                ctx.state["final_content"] = final_content
                return ctx

            for call in response.tool_calls:
                tool_call = ToolCall(
                    id=call.get("id", ""),
                    name=call.get("name", ""),
                    arguments=call.get("arguments", {}),
                )
                log.append("tool_call", call=tool_call.model_dump())

                result = self.tools.invoke(tool_call)
                log.append("tool_result", result=result.model_dump())

                messages.append(
                    Message(
                        role="tool",
                        content=result.output or result.error or "",
                        tool_call_id=result.tool_call_id,
                        name=result.name,
                    )
                )

        log.append("run_max_steps", steps=self.max_steps)
        ctx.state["final_content"] = final_content
        return ctx
