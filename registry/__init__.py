"""
🦾 XMRT Agent Registry Package
Multi-persona management system for autonomous AI agents
"""

from .agent_registry import (
    AgentRegistry,
    AgentRole,
    AgentStatus, 
    AgentPersona
)

__version__ = "1.0.0"
__author__ = "XMRT DAO"

__all__ = [
    "AgentRegistry",
    "AgentRole", 
    "AgentStatus",
    "AgentPersona"
]
