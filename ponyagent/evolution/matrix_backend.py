"""MATRIX-style code generator backend."""

from __future__ import annotations

from typing import Any

from ponyagent.capabilities.code_generator import CodeGenerator
from ponyagent.capabilities.sandbox import CodeSandbox
from ponyagent.evolution.protocol import EvolutionProtocol
from ponyagent.types.skill import Skill


class MatrixCodeBackend(EvolutionProtocol):
    """Code generation + sandbox validation (MATRIX-inspired)."""

    name = "matrix_codegen"

    def __init__(self) -> None:
        self.sandbox = CodeSandbox()
        self.generator = CodeGenerator(self.sandbox)
        self._skills: dict[str, Skill] = {}

    async def learn(self, task: str, result: Any, success: bool) -> Skill | None:
        """If the task looks like code generation, validate and install."""
        if not isinstance(result, str):
            return None
        safe, err = self.sandbox.check_ast(result)
        if not safe:
            return None
        import hashlib
        sid = hashlib.sha256(result.encode()).hexdigest()[:12]
        skill = Skill(
            id=sid,
            name=f"code_{sid[:6]}",
            description=task,
            code=result,
        )
        self._skills[skill.id] = skill
        return skill

    async def search(self, query: str, top_k: int = 5) -> list[Skill]:
        q = query.lower()
        matched = [s for s in self._skills.values() if q in s.description.lower()]
        return matched[:top_k]

    async def install(self, skill: Skill) -> bool:
        safe, err = self.sandbox.check_ast(skill.code)
        if not safe:
            return False
        self._skills[skill.id] = skill
        return True

    def list_skills(self) -> list[Skill]:
        return list(self._skills.values())
