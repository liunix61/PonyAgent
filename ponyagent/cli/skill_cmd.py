"""Skill management CLI."""

from __future__ import annotations

import asyncio
import json

from ponyagent.capabilities.skill_graph import SkillGraph, Skill


def list_skills() -> list[Skill]:
    """List all installed skills."""
    sg = SkillGraph()
    return sg.skills


def show_skill(skill_id: str) -> Skill | None:
    """Show details of a skill (by id, exact match)."""
    sg = SkillGraph()
    return next((s for s in sg.skills if s.id == skill_id), None)


def install_skill(skill: Skill) -> bool:
    """Install a skill."""
    sg = SkillGraph()
    return asyncio.run(sg.install(skill))


def delete_skill(skill_id: str) -> bool:
    """Delete a skill (returns True if removed)."""
    sg = SkillGraph()
    if any(s.id == skill_id for s in sg.skills):
        sg._skills.pop(skill_id, None)
        return True
    return False


def export_skills() -> str:
    """Export all skills as JSON."""
    sg = SkillGraph()
    return json.dumps([s.model_dump(mode="json") for s in sg.skills], indent=2, default=str)
