"""Orchestration package - 6 orchestration modes with unified protocol."""

from ponyagent.orchestration.blackboard import Blackboard
from ponyagent.orchestration.crew import CrewOrchestrator
from ponyagent.orchestration.dag_pipeline import DAGPipelineOrchestrator
from ponyagent.orchestration.graph import StateGraphOrchestrator
from ponyagent.orchestration.protocol_stack import ProtocolStackOrchestrator
from ponyagent.orchestration.registry import (
    get_orchestrator,
    list_orchestrators,
    register_orchestrator,
)
from ponyagent.orchestration.turn_manager import TurnManagerOrchestrator

__all__ = [
    "Blackboard",
    "CrewOrchestrator",
    "DAGPipelineOrchestrator",
    "ProtocolStackOrchestrator",
    "StateGraphOrchestrator",
    "TurnManagerOrchestrator",
    "get_orchestrator",
    "list_orchestrators",
    "register_orchestrator",
]

# Register built-in orchestrators
register_orchestrator("graph", StateGraphOrchestrator)
register_orchestrator("crew", CrewOrchestrator)
register_orchestrator("turn", TurnManagerOrchestrator)
register_orchestrator("protocol_stack", ProtocolStackOrchestrator)
register_orchestrator("dag_pipeline", DAGPipelineOrchestrator)
