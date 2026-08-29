"""Evolution backends package."""

from ponyagent.evolution.hermes_backend import HermesSkillBackend
from ponyagent.evolution.lesson_backend import LessonBackend
from ponyagent.evolution.memory_backend import UniAgentsMemoryBackend
from ponyagent.evolution.matrix_backend import MatrixCodeBackend
from ponyagent.evolution.protocol import EvolutionProtocol, EvolutionRegistry, get_evolution, list_evolutions, register_evolution
from ponyagent.evolution.replay_backend import ReplayBackend

__all__ = [
    "EvolutionProtocol",
    "EvolutionRegistry",
    "HermesSkillBackend",
    "LessonBackend",
    "MatrixCodeBackend",
    "ReplayBackend",
    "UniAgentsMemoryBackend",
    "get_evolution",
    "list_evolutions",
    "register_evolution",
]

# Auto-register built-in backends
register_evolution("hermes_skills", HermesSkillBackend)
register_evolution("matrix_codegen", MatrixCodeBackend)
register_evolution("uniagents_memory", UniAgentsMemoryBackend)
register_evolution("replay", ReplayBackend)
register_evolution("lesson_pool", LessonBackend)
