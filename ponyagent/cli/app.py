"""CLI entry point."""

from __future__ import annotations

import argparse
import asyncio
import sys

from ponyagent import PonyAgent
from ponyagent.models.stub_adapter import StubLLMAdapter
from ponyagent.types.message import Message


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ponyagent",
        description="PonyAgent - Lightweight multi-agent OS",
    )
    parser.add_argument("--version", action="version", version="0.1.0")
    parser.add_argument("goal", nargs="?", help="Goal to accomplish")
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--base-url", default="")
    parser.add_argument(
        "--orchestrator",
        default="graph",
        choices=["graph", "crew", "turn", "dag_pipeline"],
    )
    parser.add_argument("--max-steps", type=int, default=10)
    parser.add_argument("--system-prompt", default="")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.goal:
        parser.print_help()
        raise SystemExit(0)

    async def run() -> None:
        if args.api_key:
            from ponyagent.models.openai_adapter import OpenAIAdapter

            llm = OpenAIAdapter(
                model=args.model,
                api_key=args.api_key,
                base_url=args.base_url or "https://api.openai.com/v1",
            )
        else:
            llm = StubLLMAdapter()

        agent = PonyAgent(
            model=args.model,
            llm=llm,
            orchestrator=args.orchestrator,
            max_steps=args.max_steps,
            system_prompt=args.system_prompt,
        )
        ctx = await agent.arun(args.goal)
        content = ctx.state.get("final_content", "")
        print(f"[PonyAgent {ctx.step} steps] {content}")

    asyncio.run(run())


if __name__ == "__main__":
    main()
