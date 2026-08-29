"""Hermes-style skill backend - Skill CRUD + triggers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ponyagent.evolution.protocol import EvolutionProtocol
from ponyagent.types.skill import Skill

_DEFAULT_SKILLS_PATH = Path.home() / ".hermes" / "skills" / "ponyagent"


class HermesSkillBackend(EvolutionProtocol):
    """Skill CRUD with file persistence (Hermes-inspired)."""

    name = "hermes_skills"

    def __init__(self, skills_dir: Path | str | None = None) -> None:
        self.skills_dir = Path(skills_dir) if skills_dir else _DEFAULT_SKILLS_PATH
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._skills: dict[str, Skill] = {}
        self._load()

    def _load(self) -> None:
        for p in self.skills_dir.glob("*.json"):
            try:
                skill = Skill.model_validate_json(p.read_text(encoding="utf-8"))
                self._skills[skill.id] = skill
            except Exception:
                continue

    def _save(self, skill: Skill) -> None:
        p = self.skills_dir / f"{skill.id}.json"
        p.write_text(skill.model_dump_json(indent=2), encoding="utf-8")

    async def learn(self, task: str, result: Any, success: bool) -> Skill | None:
        """On success, extract a Skill. On failure, return None."""
        if not success:
            return None
        import hashlib
        sid = hashlib.sha256(task.encode()).hexdigest()[:12]
        skill = Skill(
            id=sid,
            name=task[:50],
            description=task,
            code=str(result)[:2000],
        )
        self._skills[skill.id] = skill
        self._save(skill)
        return skill

    async def search(self, query: str, top_k: int = 5) -> list[Skill]:
        q = query.lower()
        matched = [s for s in self._skills.values() if q in s.name.lower() or q in s.description.lower()]
        return matched[:top_k]

    async def install(self, skill: Skill) -> bool:
        self._skills[skill.id] = skill
        self._save(skill)
        return True

    def list_skills(self) -> list[Skill]:
        return list(self._skills.values())

    def delete(self, id: str) -> bool:
        if id in self._skills:
            del self._skills[id]
            p = self.skills_dir / f"{id}.json"
            if p.exists():
                p.unlink()
            return True
        return False
