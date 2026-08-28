"""Code sandbox - safe execution of generated code (fx + MATRIX inspired)."""

from __future__ import annotations

import ast
import json
from typing import Any

from pydantic import BaseModel, Field


class SandboxResult(BaseModel):
    """Result of sandboxed code execution."""

    success: bool
    output: str | None = None
    error: str | None = None


class CodeSandbox:
    """Safe code execution sandbox.

    Uses AST analysis to detect dangerous operations,
    then executes in a restricted namespace.
    """

    DANGEROUS_NODES: list[str] = [
        "Import",
        "ImportFrom",
        "Execute",  # exec
    ]
    DANGEROUS_NAMES: set[str] = {
        "exec",
        "eval",
        "compile",
        "__import__",
        "open",
        "os",
        "sys",
        "subprocess",
        "shutil",
    }

    def __init__(self, timeout: float = 5.0) -> None:
        self.timeout = timeout
        self._results: list[SandboxResult] = []

    def check_ast(self, code: str) -> tuple[bool, str | None]:
        """Check code for dangerous operations via AST analysis.

        Returns (is_safe, error_message).
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {e}"

        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                return False, "Imports not allowed in sandbox"

            # Check dangerous function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.DANGEROUS_NAMES:
                        return False, f"Dangerous function: {node.func.id}"

        return True, None

    async def execute(self, code: str, **context: Any) -> SandboxResult:
        """Execute code in a restricted sandbox.

        First validates via AST, then runs in a safe namespace.
        """
        is_safe, error = self.check_ast(code)
        if not is_safe:
            result = SandboxResult(success=False, error=error)
            self._results.append(result)
            return result

        safe_globals = {
            "__builtins__": {
                "len": len,
                "range": range,
                "print": print,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "bool": bool,
                "sum": sum,
                "min": min,
                "max": max,
                "sorted": sorted,
                "abs": abs,
                "round": round,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "any": any,
                "all": all,
                "isinstance": isinstance,
                "type": type,
                "Exception": Exception,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "KeyError": KeyError,
                "IndexError": IndexError,
                "True": True,
                "False": False,
                "None": None,
            },
            "__name__": "__sandbox__",
        }
        safe_globals.update(context)

        try:
            output_lines: list[str] = []

            def safe_print(*args: Any) -> None:
                output_lines.append(" ".join(str(a) for a in args))

            safe_globals["__builtins__"]["print"] = safe_print

            exec(code, safe_globals)  # noqa: S102
            output = "\n".join(output_lines) if output_lines else None

            result = SandboxResult(success=True, output=output)
            self._results.append(result)
            return result

        except Exception as e:
            result = SandboxResult(success=False, error=str(e))
            self._results.append(result)
            return result

    @property
    def history(self) -> list[SandboxResult]:
        """Return execution history."""
        return list(self._results)

    def clear(self) -> None:
        """Clear execution history."""
        self._results.clear()
