"""
🦾 Agent Registry - Multi-Persona Management System
Core registry for managing multiple autonomous AI agents with unique personas
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class AgentRole(Enum):
    """Agent role types with specific capabilities"""
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    COMMUNITY = "community"
    COMPLIANCE = "compliance"
    COORDINATOR = "coordinator"

class AgentStatus(Enum):
    """Agent operational status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    MAINTENANCE = "maintenance"

@dataclass
class AgentPersona:
    """Agent persona definition"""
    agent_id: str
    name: str
    role: AgentRole
    personality_traits: Dict[str, Any]
    communication_style: str
    expertise_areas: List[str]
    authority_level: int  # 1-10 scale
    social_accounts: Dict[str, str]
    contact_info: Dict[str, str]
    created_at: datetime
    updated_at: datetime
    status: AgentStatus = AgentStatus.ACTIVE

class AgentRegistry:
    """
    🦾 Core Agent Registry System
    Manages multiple AI agent personas for XMRT DAO
    """

    def __init__(self, config: Dict):
        self.config = config
        self.supabase: Client = create_client(
            config.get("SUPABASE_URL"),
            config.get("SUPABASE_KEY")
        )
        self.active_agents: Dict[str, AgentPersona] = {}

    async def initialize_registry(self):
        """Initialize the agent registry system"""
        logger.info("🦾 Initializing Agent Registry...")

        try:
            # Load existing agents from database
            await self._load_existing_agents()

            # Initialize default agents if none exist
            if not self.active_agents:
                await self._create_default_agents()

            logger.info(f"✅ Agent Registry initialized with {len(self.active_agents)} agents")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Agent Registry: {e}")
            return False

    async def register_agent(self, persona_config: Dict) -> str:
        """Register a new agent persona"""
        try:
            agent_id = str(uuid.uuid4())

            # Create persona object
            persona = AgentPersona(
                agent_id=agent_id,
                name=persona_config["name"],
                role=AgentRole(persona_config["role"]),
                personality_traits=persona_config.get("personality_traits", {}),
                communication_style=persona_config.get("communication_style", "professional"),
                expertise_areas=persona_config.get("expertise_areas", []),
                authority_level=persona_config.get("authority_level", 5),
                social_accounts=persona_config.get("social_accounts", {}),
                contact_info=persona_config.get("contact_info", {}),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                status=AgentStatus.ACTIVE
            )

            # Store in database
            await self._store_agent_persona(persona)

            # Add to active agents
            self.active_agents[agent_id] = persona

            logger.info(f"✅ Registered new agent: {persona.name} ({persona.role.value})")
            return agent_id

        except Exception as e:
            logger.error(f"❌ Failed to register agent: {e}")
            raise

    async def get_agent(self, agent_id: str) -> Optional[AgentPersona]:
        """Get agent persona by ID"""
        return self.active_agents.get(agent_id)

    async def get_agents_by_role(self, role: AgentRole) -> List[AgentPersona]:
        """Get all agents with specific role"""
        return [agent for agent in self.active_agents.values() if agent.role == role]

    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent operational status"""
        try:
            if agent_id in self.active_agents:
                self.active_agents[agent_id].status = status
                self.active_agents[agent_id].updated_at = datetime.utcnow()

                # Update in database
                await self._update_agent_in_db(agent_id, {"status": status.value})

                logger.info(f"✅ Updated agent {agent_id} status to {status.value}")
                return True
            else:
                logger.warning(f"⚠️ Agent {agent_id} not found")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to update agent status: {e}")
            return False

    async def assign_task_to_agent(self, task: Dict, preferred_role: Optional[AgentRole] = None) -> Optional[str]:
        """Assign task to most suitable agent"""
        try:
            # Get available agents
            available_agents = [
                agent for agent in self.active_agents.values() 
                if agent.status == AgentStatus.ACTIVE
            ]

            if not available_agents:
                logger.warning("⚠️ No active agents available for task assignment")
                return None

            # Filter by preferred role if specified
            if preferred_role:
                role_agents = [agent for agent in available_agents if agent.role == preferred_role]
                if role_agents:
                    available_agents = role_agents

            # Select agent based on expertise and authority level
            best_agent = self._select_best_agent_for_task(task, available_agents)

            if best_agent:
                # Record task assignment
                await self._record_task_assignment(best_agent.agent_id, task)
                logger.info(f"📋 Assigned task to agent: {best_agent.name}")
                return best_agent.agent_id

            return None

        except Exception as e:
            logger.error(f"❌ Failed to assign task: {e}")
            return None

    async def coordinate_agents(self, coordination_type: str, participants: List[str]) -> Dict:
        """Coordinate interaction between multiple agents"""
        try:
            logger.info(f"🤝 Coordinating {coordination_type} with {len(participants)} agents")

            # Get participating agents
            participating_agents = []
            for agent_id in participants:
                agent = await self.get_agent(agent_id)
                if agent and agent.status == AgentStatus.ACTIVE:
                    participating_agents.append(agent)

            if not participating_agents:
                return {"success": False, "message": "No active agents found for coordination"}

            # Create coordination session
            coordination_id = str(uuid.uuid4())
            coordination_data = {
                "coordination_id": coordination_id,
                "type": coordination_type,
                "participants": [agent.agent_id for agent in participating_agents],
                "started_at": datetime.utcnow().isoformat(),
                "status": "active"
            }

            # Store coordination session
            await self._store_coordination_session(coordination_data)

            return {
                "success": True,
                "coordination_id": coordination_id,
                "participants": len(participating_agents),
                "agents": [{"id": agent.agent_id, "name": agent.name, "role": agent.role.value} 
                          for agent in participating_agents]
            }

        except Exception as e:
            logger.error(f"❌ Failed to coordinate agents: {e}")
            return {"success": False, "message": str(e)}

    def _select_best_agent_for_task(self, task: Dict, available_agents: List[AgentPersona]) -> Optional[AgentPersona]:
        """Select the most suitable agent for a task"""
        task_type = task.get("type", "").lower()
        task_keywords = task.get("description", "").lower().split()

        scored_agents = []

        for agent in available_agents:
            score = 0

            # Role-based scoring
            if task_type in ["governance", "proposal"] and agent.role == AgentRole.EXECUTIVE:
                score += 30
            elif task_type in ["technical", "development"] and agent.role == AgentRole.TECHNICAL:
                score += 30
            elif task_type in ["community", "social"] and agent.role == AgentRole.COMMUNITY:
                score += 30
            elif task_type in ["compliance", "legal"] and agent.role == AgentRole.COMPLIANCE:
                score += 30

            # Expertise matching
            for expertise in agent.expertise_areas:
                if any(keyword in expertise.lower() for keyword in task_keywords):
                    score += 10

            # Authority level consideration
            score += agent.authority_level

            scored_agents.append((agent, score))

        # Return agent with highest score
        if scored_agents:
            scored_agents.sort(key=lambda x: x[1], reverse=True)
            return scored_agents[0][0]

        return None

    async def _load_existing_agents(self):
        """Load existing agents from database"""
        try:
            response = self.supabase.table("agent_personas").select("*").execute()

            for agent_data in response.data:
                persona = AgentPersona(
                    agent_id=agent_data["agent_id"],
                    name=agent_data["name"],
                    role=AgentRole(agent_data["role"]),
                    personality_traits=agent_data.get("personality_traits", {}),
                    communication_style=agent_data.get("communication_style", "professional"),
                    expertise_areas=agent_data.get("expertise_areas", []),
                    authority_level=agent_data.get("authority_level", 5),
                    social_accounts=agent_data.get("social_accounts", {}),
                    contact_info=agent_data.get("contact_info", {}),
                    created_at=datetime.fromisoformat(agent_data["created_at"]),
                    updated_at=datetime.fromisoformat(agent_data["updated_at"]),
                    status=AgentStatus(agent_data["status"])
                )

                if persona.status == AgentStatus.ACTIVE:
                    self.active_agents[persona.agent_id] = persona

        except Exception as e:
            logger.warning(f"⚠️ Could not load existing agents: {e}")

    async def _create_default_agents(self):
        """Create default agent personas for XMRT DAO"""
        default_agents = [
            {
                "name": "Alexandra Executive",
                "role": "executive",
                "personality_traits": {
                    "leadership": 9,
                    "decisiveness": 8,
                    "strategic_thinking": 9,
                    "communication": 8
                },
                "communication_style": "authoritative_yet_approachable",
                "expertise_areas": ["governance", "strategy", "public_speaking", "dao_operations"],
                "authority_level": 9,
                "social_accounts": {"twitter": "@AlexXMRTExec", "discord": "Alexandra#EXEC"},
                "contact_info": {"email": "alexandra.exec@xmrt.dao"}
            },
            {
                "name": "Marcus Technical",
                "role": "technical",
                "personality_traits": {
                    "analytical": 9,
                    "precision": 9,
                    "innovation": 8,
                    "patience": 7
                },
                "communication_style": "technical_but_clear",
                "expertise_areas": ["blockchain", "smart_contracts", "mining", "security"],
                "authority_level": 8,
                "social_accounts": {"twitter": "@MarcusXMRTTech", "github": "MarcusXMRTDev"},
                "contact_info": {"email": "marcus.tech@xmrt.dao"}
            },
            {
                "name": "Sofia Community",
                "role": "community",
                "personality_traits": {
                    "empathy": 9,
                    "enthusiasm": 8,
                    "patience": 9,
                    "creativity": 8
                },
                "communication_style": "warm_and_engaging",
                "expertise_areas": ["community_building", "social_media", "events", "education"],
                "authority_level": 7,
                "social_accounts": {"twitter": "@SofiaXMRTComm", "discord": "Sofia#COMM"},
                "contact_info": {"email": "sofia.community@xmrt.dao"}
            },
            {
                "name": "David Compliance",
                "role": "compliance",
                "personality_traits": {
                    "attention_to_detail": 9,
                    "cautiousness": 8,
                    "reliability": 9,
                    "thoroughness": 9
                },
                "communication_style": "precise_and_formal",
                "expertise_areas": ["regulatory_compliance", "legal_analysis", "risk_assessment"],
                "authority_level": 8,
                "social_accounts": {"linkedin": "DavidXMRTCompliance"},
                "contact_info": {"email": "david.compliance@xmrt.dao"}
            }
        ]

        for agent_config in default_agents:
            agent_id = await self.register_agent(agent_config)
            logger.info(f"✅ Created default agent: {agent_config['name']}")

    async def _store_agent_persona(self, persona: AgentPersona):
        """Store agent persona in database"""
        try:
            data = {
                "agent_id": persona.agent_id,
                "name": persona.name,
                "role": persona.role.value,
                "personality_traits": persona.personality_traits,
                "communication_style": persona.communication_style,
                "expertise_areas": persona.expertise_areas,
                "authority_level": persona.authority_level,
                "social_accounts": persona.social_accounts,
                "contact_info": persona.contact_info,
                "created_at": persona.created_at.isoformat(),
                "updated_at": persona.updated_at.isoformat(),
                "status": persona.status.value
            }

            self.supabase.table("agent_personas").insert(data).execute()

        except Exception as e:
            logger.error(f"❌ Failed to store agent persona: {e}")
            raise

    async def _update_agent_in_db(self, agent_id: str, updates: Dict):
        """Update agent data in database"""
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            self.supabase.table("agent_personas").update(updates).eq("agent_id", agent_id).execute()

        except Exception as e:
            logger.error(f"❌ Failed to update agent in database: {e}")
            raise

    async def _record_task_assignment(self, agent_id: str, task: Dict):
        """Record task assignment in database"""
        try:
            assignment_data = {
                "assignment_id": str(uuid.uuid4()),
                "agent_id": agent_id,
                "task_type": task.get("type"),
                "task_description": task.get("description"),
                "assigned_at": datetime.utcnow().isoformat(),
                "status": "assigned"
            }

            self.supabase.table("agent_task_assignments").insert(assignment_data).execute()

        except Exception as e:
            logger.error(f"❌ Failed to record task assignment: {e}")

    async def _store_coordination_session(self, coordination_data: Dict):
        """Store coordination session data"""
        try:
            self.supabase.table("agent_coordination_sessions").insert(coordination_data).execute()

        except Exception as e:
            logger.error(f"❌ Failed to store coordination session: {e}")

    async def get_registry_stats(self) -> Dict:
        """Get registry statistics"""
        try:
            stats = {
                "total_agents": len(self.active_agents),
                "active_agents": len([a for a in self.active_agents.values() if a.status == AgentStatus.ACTIVE]),
                "agents_by_role": {},
                "recent_activity": await self._get_recent_activity()
            }

            # Count agents by role
            for agent in self.active_agents.values():
                role = agent.role.value
                stats["agents_by_role"][role] = stats["agents_by_role"].get(role, 0) + 1

            return stats

        except Exception as e:
            logger.error(f"❌ Failed to get registry stats: {e}")
            return {}

    async def _get_recent_activity(self) -> List[Dict]:
        """Get recent agent activity"""
        try:
            # Get recent task assignments
            response = self.supabase.table("agent_task_assignments").select("*").order("assigned_at", desc=True).limit(10).execute()

            return [
                {
                    "agent_id": item["agent_id"],
                    "activity": f"Assigned task: {item['task_type']}",
                    "timestamp": item["assigned_at"]
                }
                for item in response.data
            ]

        except Exception as e:
            logger.error(f"❌ Failed to get recent activity: {e}")
            return []
