"""Code generator - generates and validates code (MATRIX inspired)."""

from __future__ import annotations

from typing import Any, Callable

from ponyagent.capabilities.sandbox import CodeSandbox, SandboxResult


class CodeGenerator:
    """Generates and validates code snippets.

    Uses a sandbox to test generated code before accepting it.
    """

    def __init__(self, sandbox: CodeSandbox | None = None) -> None:
        self.sandbox = sandbox or CodeSandbox()

    async def generate(
        self,
        description: str,
        language: str = "python",
        context: dict[str, Any] | None = None,
    ) -> str:
        """Generate code from a description.

        Stub implementation - replace with LLM call in production.
        """
        ctx_str = ""
        if context:
            ctx_str = f"# Context: {context}"
        return f"""# Generated: {description}
{ctx_str}
def solution():
    pass
"""

    async def validate(self, code: str) -> SandboxResult:
        """Validate code by executing in sandbox."""
        return await self.sandbox.execute(code)

    async def generate_and_validate(
        self,
        description: str,
        test_fn: Callable | None = None,
        **context: Any,
    ) -> tuple[str, SandboxResult]:
        """Generate code and validate it.

        Returns (code, validation_result).
        """
        code = await self.generate(description, context=context)
        result = await self.validate(code)
        return code, result
