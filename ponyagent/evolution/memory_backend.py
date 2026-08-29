"""UniAgents-style memory system backend (three-layer memory + vector)."""

from __future__ import annotations

from typing import Any

from ponyagent.evolution.protocol import EvolutionProtocol
from ponyagent.memory.episodic import EpisodicMemory
from ponyagent.memory.long_term import LongTermMemory
from ponyagent.memory.short_term import ShortTermMemory
from ponyagent.types.message import Message
from ponyagent.types.skill import Skill


class UniAgentsMemoryBackend(EvolutionProtocol):
    """Three-layer memory backend (UniAgents-inspired).

    Composes short-term (deque), long-term (AIDB/SQLite), and
    episodic (AIMEM/JSONL) into a single Evolution interface.
    """

    name = "uniagents_memory"

    def __init__(
        self,
        aidb_path: str | None = None,
        aimem_path: str | None = None,
        short_term_size: int = 50,
    ) -> None:
        self.short_term = ShortTermMemory(max_messages=short_term_size)
        self.long_term = LongTermMemory(db_path=aidb_path) if aidb_path else LongTermMemory()
        self.episodic = EpisodicMemory(path=aimem_path) if aimem_path else EpisodicMemory()
        self._skills: dict[str, Skill] = {}

    async def learn(self, task: str, result: Any, success: bool) -> Skill | None:
        """Learn by adding an episode and a skill (on success)."""
        import hashlib

        # Always record an episode
        self.episodic.add(
            content=f"{task} -> {'success' if success else 'failure'}",
            tags=["task", "outcome"],
            metadata={"task": task, "success": success, "result_preview": str(result)[:200]},
        )
        # Persist in long-term memory
        await self.long_term.add(
            content=f"{task} (success={success})",
            metadata={"task": task, "success": success},
            source="evolution",
        )
        if not success:
            return None
        sid = hashlib.sha256(task.encode()).hexdigest()[:12]
        skill = Skill(id=sid, name=task[:50], description=task, code=str(result)[:2000])
        self._skills[skill.id] = skill
        return skill

    async def search(self, query: str, top_k: int = 5) -> list[Skill]:
        q = query.lower()
        matched = [s for s in self._skills.values() if q in s.description.lower()]
        return matched[:top_k]

    async def install(self, skill: Skill) -> bool:
        self._skills[skill.id] = skill
        return True

    async def get_lessons(self, task: str) -> list[dict[str, Any]]:
        """Episodes are lessons."""
        return self.episodic.search(task, top_k=5)

    def list_skills(self) -> list[Skill]:
        return list(self._skills.values())
