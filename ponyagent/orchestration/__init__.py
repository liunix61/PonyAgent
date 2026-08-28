"""Orchestration package - 5 orchestration modes with unified protocol."""

from ponyagent.orchestration.blackboard import Blackboard
from ponyagent.orchestration.crew import CrewOrchestrator
from ponyagent.orchestration.dag_pipeline import DAGPipelineOrchestrator
from ponyagent.orchestration.graph import StateGraphOrchestrator
from ponyagent.orchestration.registry import (
    get_orchestrator,
    list_orchestrators,
    register_orchestrator,
)
from ponyagent.orchestration.turn_manager import TurnManagerOrchestrator

# Register built-in orchestrators
register_orchestrator("graph")(StateGraphOrchestrator)
register_orchestrator("crew")(CrewOrchestrator)
register_orchestrator("turn")(TurnManagerOrchestrator)
register_orchestrator("dag_pipeline")(DAGPipelineOrchestrator)

__all__ = [
    "Blackboard",
    "CrewOrchestrator",
    "DAGPipelineOrchestrator",
    "StateGraphOrchestrator",
    "TurnManagerOrchestrator",
    "get_orchestrator",
    "list_orchestrators",
    "register_orchestrator",
]
