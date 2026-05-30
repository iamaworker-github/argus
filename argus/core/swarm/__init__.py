"""
Argus Swarm — Stigmergic blackboard architecture.

Pentest-Swarm-AI se inspired: agents coordinate via shared blackboard
with pheromone weights, NOT via central planner. Emergent attack paths.
"""
from argus.core.swarm.blackboard import (
    BlackboardEntry, BlackboardQuery, Blackboard,
    MemoryBlackboard, get_blackboard,
)
from argus.core.swarm.pheromone import PheromoneConfig, pheromone_weight
from argus.core.swarm.trigger import TriggerPredicate, agent_trigger
from argus.core.swarm.scheduler import SwarmScheduler, SwarmAgent, get_scheduler

__all__ = [
    "BlackboardEntry", "BlackboardQuery", "Blackboard",
    "MemoryBlackboard", "get_blackboard",
    "PheromoneConfig", "pheromone_weight",
    "TriggerPredicate", "agent_trigger",
    "SwarmScheduler", "SwarmAgent", "get_scheduler",
]
