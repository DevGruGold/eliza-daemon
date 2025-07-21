#!/usr/bin/env python3
"""
🦾 Multi-Agent Eliza Daemon - Enhanced with Agent Registry
Manages multiple autonomous AI agents with unique personas for XMRT DAO
"""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Import existing modules (maintain compatibility)
from tasks.monitor_twitter import TwitterMonitor
from tasks.monitor_miners import MinerMonitor
from tasks.handle_rewards import RewardHandler
from tasks.governance_agent import GovernanceAgent
from tasks.notify_discord import DiscordNotifier

# Import enhanced AI brain and memory
from agent.langchain_brain import ElizaAgent
from memory.supabase_memory import SupabaseMemory

# Import new registry system
from registry.agent_registry import AgentRegistry, AgentRole, AgentStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/multi_agent_eliza.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class MultiAgentElizaDaemon:
    """
    🦾 Enhanced Multi-Agent Eliza Daemon
    Orchestrates multiple autonomous AI agents with unique personas
    """

    def __init__(self, config_path='config.json'):
        self.config = self.load_config(config_path)
        self.setup_components()
        self.running = False
        self.agent_brains: Dict[str, ElizaAgent] = {}

    def load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {config_path} not found!")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {config_path}")
            raise

    def setup_components(self):
        """Initialize all system components"""
        logger.info("🧠 Initializing Multi-Agent System...")

        # Initialize memory system
        self.memory = SupabaseMemory(self.config)

        # Initialize agent registry (NEW)
        self.agent_registry = AgentRegistry(self.config)

        # Initialize existing task modules (maintain compatibility)
        self.twitter_monitor = TwitterMonitor(self.config)
        self.miner_monitor = MinerMonitor(self.config)
        self.reward_handler = RewardHandler(self.config)
        self.governance_agent = GovernanceAgent(self.config)
        self.discord_notifier = DiscordNotifier(self.config)

        logger.info("✅ All components initialized successfully")

    async def initialize_agents(self):
        """Initialize all registered agents with their AI brains"""
        logger.info("🦾 Initializing agent personas...")

        # Initialize the agent registry
        registry_success = await self.agent_registry.initialize_registry()
        if not registry_success:
            logger.error("❌ Failed to initialize agent registry")
            return False

        # Create AI brains for each active agent
        for agent_id, persona in self.agent_registry.active_agents.items():
            try:
                # Create personalized AI brain for each agent
                agent_brain = ElizaAgent(self.config, self.memory)

                # Customize the brain based on persona
                await self._customize_agent_brain(agent_brain, persona)

                self.agent_brains[agent_id] = agent_brain
                logger.info(f"✅ Initialized AI brain for {persona.name}")

            except Exception as e:
                logger.error(f"❌ Failed to initialize brain for {persona.name}: {e}")

        logger.info(f"🧠 Initialized {len(self.agent_brains)} agent brains")
        return True

    async def _customize_agent_brain(self, brain: ElizaAgent, persona):
        """Customize AI brain based on agent persona"""
        # Add persona-specific context to the brain
        persona_context = {
            "name": persona.name,
            "role": persona.role.value,
            "personality_traits": persona.personality_traits,
            "communication_style": persona.communication_style,
            "expertise_areas": persona.expertise_areas,
            "authority_level": persona.authority_level
        }

        # Store persona context in memory for the agent
        await self.memory.store_context(f"persona_{persona.agent_id}", persona_context)

    async def listen_phase(self):
        """
        👂 Enhanced LISTEN: Gather data from all sources
        Now considers multiple agent perspectives
        """
        logger.info("👂 MULTI-AGENT LISTEN PHASE: Gathering data...")

        # Gather data from all sources concurrently (existing logic)
        tasks = [
            self.twitter_monitor.check_new_activity(),
            self.miner_monitor.get_current_stats(),
            self.governance_agent.check_pending_proposals(),
        ]

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            data = {
                'twitter_activity': results[0] if not isinstance(results[0], Exception) else None,
                'miner_stats': results[1] if not isinstance(results[1], Exception) else None,
                'governance_data': results[2] if not isinstance(results[2], Exception) else None,
                'timestamp': datetime.utcnow().isoformat(),
                'registry_stats': await self.agent_registry.get_registry_stats()
            }

            logger.info(f"📊 Data gathered from {len([k for k, v in data.items() if v is not None])} sources")
            return data

        except Exception as e:
            logger.error(f"Error in listen phase: {e}")
            return {}

    async def think_phase(self, data):
        """
        🧠 Enhanced THINK: Multi-agent decision making
        Each agent thinks independently based on their persona
        """
        logger.info("🧠 MULTI-AGENT THINK PHASE: Processing with multiple AI agents...")

        agent_decisions = {}
        coordination_needed = []

        try:
            # Each agent makes decisions based on their role and data
            for agent_id, agent_brain in self.agent_brains.items():
                persona = await self.agent_registry.get_agent(agent_id)
                if not persona or persona.status != AgentStatus.ACTIVE:
                    continue

                try:
                    # Get persona-specific decisions
                    decisions = await self._get_agent_decisions(agent_brain, persona, data)
                    agent_decisions[agent_id] = {
                        'agent_name': persona.name,
                        'agent_role': persona.role.value,
                        'decisions': decisions,
                        'timestamp': datetime.utcnow().isoformat()
                    }

                    # Check if coordination is needed
                    if self._requires_coordination(decisions):
                        coordination_needed.append(agent_id)

                except Exception as e:
                    logger.error(f"❌ Error in decision making for {persona.name}: {e}")

            # Handle inter-agent coordination if needed
            if coordination_needed:
                coordination_result = await self.agent_registry.coordinate_agents(
                    "decision_coordination", 
                    coordination_needed
                )
                agent_decisions['coordination'] = coordination_result

            logger.info(f"🎯 Decisions made by {len(agent_decisions)} agents")
            return agent_decisions

        except Exception as e:
            logger.error(f"Error in think phase: {e}")
            return {}

    async def _get_agent_decisions(self, agent_brain: ElizaAgent, persona, data):
        """Get decisions from a specific agent based on their persona"""

        # Filter data relevant to agent's role and expertise
        relevant_data = self._filter_data_for_agent(data, persona)

        # Create persona-specific prompt context
        persona_prompt_context = {
            "agent_identity": {
                "name": persona.name,
                "role": persona.role.value,
                "personality": persona.personality_traits,
                "communication_style": persona.communication_style,
                "expertise": persona.expertise_areas,
                "authority_level": persona.authority_level
            },
            "relevant_data": relevant_data
        }

        # Get decisions from the agent's brain
        decisions = await agent_brain.make_decisions(persona_prompt_context)

        return decisions

    def _filter_data_for_agent(self, data, persona):
        """Filter data based on agent's role and expertise"""
        relevant_data = data.copy()

        # Role-specific data filtering
        if persona.role == AgentRole.EXECUTIVE:
            # Executive agents care about governance, high-level metrics
            relevant_data['focus_areas'] = ['governance', 'strategic_decisions', 'community_leadership']

        elif persona.role == AgentRole.TECHNICAL:
            # Technical agents focus on mining, technical issues
            relevant_data['focus_areas'] = ['mining_stats', 'technical_issues', 'blockchain_data']

        elif persona.role == AgentRole.COMMUNITY:
            # Community agents focus on social activity, engagement
            relevant_data['focus_areas'] = ['social_activity', 'community_engagement', 'user_feedback']

        elif persona.role == AgentRole.COMPLIANCE:
            # Compliance agents focus on regulatory, legal aspects
            relevant_data['focus_areas'] = ['regulatory_compliance', 'legal_requirements', 'risk_assessment']

        return relevant_data

    def _requires_coordination(self, decisions):
        """Determine if agent decisions require coordination with other agents"""
        # Check for high-impact decisions that need coordination
        high_impact_actions = ['governance', 'treasury', 'major_announcements', 'strategic_changes']

        for decision_category, actions in decisions.items():
            if decision_category in high_impact_actions:
                return True

            # Check for decisions with high authority requirements
            if isinstance(actions, list):
                for action in actions:
                    if isinstance(action, dict) and action.get('authority_required', 0) > 7:
                        return True

        return False

    async def act_phase(self, agent_decisions):
        """
        🎬 Enhanced ACT: Execute multi-agent decisions
        Coordinates actions across different agents
        """
        logger.info("🎬 MULTI-AGENT ACT PHASE: Executing coordinated decisions...")

        all_actions_taken = []

        try:
            # Process decisions from each agent
            for agent_id, agent_data in agent_decisions.items():
                if agent_id == 'coordination':
                    continue  # Handle coordination separately

                agent_name = agent_data.get('agent_name', 'Unknown')
                decisions = agent_data.get('decisions', {})

                logger.info(f"🎬 Executing actions for {agent_name}...")

                # Execute agent-specific actions
                agent_actions = await self._execute_agent_actions(agent_id, decisions)
                all_actions_taken.extend(agent_actions)

            # Handle coordination results if present
            if 'coordination' in agent_decisions:
                coordination_actions = await self._handle_coordination_actions(agent_decisions['coordination'])
                all_actions_taken.extend(coordination_actions)

            # Log all actions taken
            for action in all_actions_taken:
                logger.info(f"✅ Action executed: {action}")

            # Enhanced Discord notification with multi-agent summary
            await self._send_multi_agent_summary(agent_decisions, all_actions_taken)

            return all_actions_taken

        except Exception as e:
            logger.error(f"Error in act phase: {e}")
            return []

    async def _execute_agent_actions(self, agent_id, decisions):
        """Execute actions for a specific agent"""
        actions_taken = []
        persona = await self.agent_registry.get_agent(agent_id)

        if not persona:
            return actions_taken

        try:
            # Execute different types of actions based on agent role
            if persona.role == AgentRole.EXECUTIVE:
                actions_taken.extend(await self._execute_executive_actions(decisions))
            elif persona.role == AgentRole.TECHNICAL:
                actions_taken.extend(await self._execute_technical_actions(decisions))
            elif persona.role == AgentRole.COMMUNITY:
                actions_taken.extend(await self._execute_community_actions(decisions))
            elif persona.role == AgentRole.COMPLIANCE:
                actions_taken.extend(await self._execute_compliance_actions(decisions))

            # Record actions in agent performance metrics
            await self._record_agent_performance(agent_id, len(actions_taken))

        except Exception as e:
            logger.error(f"❌ Error executing actions for {persona.name}: {e}")

        return actions_taken

    async def _execute_executive_actions(self, decisions):
        """Execute actions specific to executive agents"""
        actions = []

        # Handle governance proposals
        if 'proposals' in decisions:
            proposal_results = await self.governance_agent.create_proposals(decisions['proposals'])
            actions.extend(proposal_results)

        # Handle strategic communications
        if 'strategic_tweets' in decisions:
            tweet_results = await self.twitter_monitor.send_tweets(decisions['strategic_tweets'])
            actions.extend(tweet_results)

        return actions

    async def _execute_technical_actions(self, decisions):
        """Execute actions specific to technical agents"""
        actions = []

        # Handle technical notifications
        if 'technical_alerts' in decisions:
            for alert in decisions['technical_alerts']:
                await self.discord_notifier.send_notifications([{
                    'channel': 'technical',
                    'message': alert.get('message'),
                    'priority': 'high'
                }])
                actions.append(f"Technical alert sent: {alert.get('title')}")

        return actions

    async def _execute_community_actions(self, decisions):
        """Execute actions specific to community agents"""
        actions = []

        # Handle community engagement
        if 'community_tweets' in decisions:
            tweet_results = await self.twitter_monitor.send_tweets(decisions['community_tweets'])
            actions.extend(tweet_results)

        # Handle rewards distribution
        if 'community_rewards' in decisions:
            reward_results = await self.reward_handler.distribute_rewards(decisions['community_rewards'])
            actions.extend(reward_results)

        return actions

    async def _execute_compliance_actions(self, decisions):
        """Execute actions specific to compliance agents"""
        actions = []

        # Handle compliance notifications
        if 'compliance_alerts' in decisions:
            for alert in decisions['compliance_alerts']:
                await self.discord_notifier.send_notifications([{
                    'channel': 'compliance',
                    'message': alert.get('message'),
                    'priority': 'urgent'
                }])
                actions.append(f"Compliance alert sent: {alert.get('title')}")

        return actions

    async def _handle_coordination_actions(self, coordination_data):
        """Handle actions that require multi-agent coordination"""
        actions = []

        if coordination_data.get('success'):
            coordination_id = coordination_data.get('coordination_id')
            actions.append(f"Multi-agent coordination session {coordination_id} completed")

        return actions

    async def _record_agent_performance(self, agent_id, actions_count):
        """Record performance metrics for an agent"""
        try:
            # This would integrate with your performance tracking system
            performance_data = {
                'agent_id': agent_id,
                'actions_completed': actions_count,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Store in memory/database
            await self.memory.store_context(f"performance_{agent_id}", performance_data)

        except Exception as e:
            logger.error(f"❌ Failed to record performance for agent {agent_id}: {e}")

    async def _send_multi_agent_summary(self, agent_decisions, all_actions):
        """Send enhanced Discord summary with multi-agent information"""
        try:
            summary_message = f"""
🦾 **Multi-Agent Cycle Summary**
📊 **Agents Active**: {len([k for k in agent_decisions.keys() if k != 'coordination'])}
🎬 **Total Actions**: {len(all_actions)}
🤝 **Coordination**: {'Yes' if 'coordination' in agent_decisions else 'No'}

**Agent Breakdown**:
"""

            for agent_id, agent_data in agent_decisions.items():
                if agent_id == 'coordination':
                    continue

                agent_name = agent_data.get('agent_name', 'Unknown')
                role = agent_data.get('agent_role', 'Unknown')
                decision_count = len(agent_data.get('decisions', {}))

                summary_message += f"• **{agent_name}** ({role}): {decision_count} decisions\n"

            await self.discord_notifier.send_notifications([{
                'channel': 'general',
                'message': summary_message,
                'priority': 'normal'
            }])

        except Exception as e:
            logger.error(f"❌ Failed to send multi-agent summary: {e}")

    async def sleep_phase(self, cycle_data):
        """
        💤 Enhanced SLEEP: Log multi-agent cycle and wait
        """
        cycle_summary = {
            'cycle_completed_at': datetime.utcnow().isoformat(),
            'active_agents': len([k for k in cycle_data.get('agent_decisions', {}).keys() if k != 'coordination']),
            'total_decisions': sum(len(data.get('decisions', {})) for data in cycle_data.get('agent_decisions', {}).values() if isinstance(data, dict) and 'decisions' in data),
            'total_actions': len(cycle_data.get('actions', [])),
            'coordination_sessions': 1 if 'coordination' in cycle_data.get('agent_decisions', {}) else 0
        }

        # Store enhanced cycle summary
        await self.memory.store_cycle_summary(cycle_summary)

        logger.info(f"💤 MULTI-AGENT SLEEP: Cycle complete. Next cycle in 10 minutes...")
        logger.info(f"📊 Enhanced Cycle Summary: {cycle_summary}")

        # Sleep for 10 minutes (600 seconds)
        await asyncio.sleep(600)

    async def autonomous_loop(self):
        """
        🔄 Enhanced autonomous decision loop with multi-agent coordination
        Listen → Think (Multi-Agent) → Act (Coordinated) → Sleep
        """
        logger.info("🦾 Multi-Agent Eliza Daemon starting autonomous operation!")

        # Initialize all agents first
        agents_initialized = await self.initialize_agents()
        if not agents_initialized:
            logger.error("❌ Failed to initialize agents. Shutting down.")
            return

        cycle_count = 0
        self.running = True

        while self.running:
            try:
                cycle_count += 1
                logger.info(f"🔄 Starting Multi-Agent Cycle #{cycle_count}")

                # LISTEN: Gather data (enhanced)
                listen_data = await self.listen_phase()

                # THINK: Multi-agent decision making
                agent_decisions = await self.think_phase(listen_data)

                # ACT: Execute coordinated actions
                actions = await self.act_phase(agent_decisions)

                # Prepare enhanced cycle data
                cycle_data = {
                    'listen_data': listen_data,
                    'agent_decisions': agent_decisions,
                    'actions': actions
                }

                # SLEEP: Log and wait
                await self.sleep_phase(cycle_data)

            except KeyboardInterrupt:
                logger.info("🛑 Shutdown signal received")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                await asyncio.sleep(60)  # Short sleep before retry

    def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Multi-Agent Eliza Daemon shutting down...")
        self.running = False

async def main():
    """Main entry point"""
    daemon = MultiAgentElizaDaemon()

    try:
        await daemon.autonomous_loop()
    except KeyboardInterrupt:
        daemon.shutdown()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        daemon.shutdown()

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    # Run Enhanced Multi-Agent Eliza
    asyncio.run(main())
