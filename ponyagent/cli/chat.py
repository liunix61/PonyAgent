"""Interactive chat CLI."""

from __future__ import annotations

import asyncio

from ponyagent import PonyAgent
from ponyagent.models.stub_adapter import StubLLMAdapter
from ponyagent.types.message import Message


async def chat_loop(agent: PonyAgent) -> None:
    """Run an interactive chat loop with the agent."""
    print("PonyAgent chat (type 'exit' to quit)")
    while True:
        try:
            user_input = input("\n> ")
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            break
        ctx = await agent.arun(user_input)
        content = ctx.state.get("final_content", "")
        print(f"\n[agent] {content}")


def start_chat(
    model: str = "gpt-4o",
    api_key: str = "",
    orchestrator: str = "graph",
    max_steps: int = 10,
) -> None:
    """Start an interactive chat session."""
    if api_key:
        from ponyagent.models.openai_adapter import OpenAIAdapter
        llm = OpenAIAdapter(model=model, api_key=api_key)
    else:
        llm = StubLLMAdapter()

    agent = PonyAgent(
        model=model,
        llm=llm,
        orchestrator=orchestrator,
        max_steps=max_steps,
    )
    asyncio.run(chat_loop(agent))


if __name__ == "__main__":
    start_chat()
