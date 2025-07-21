"""
🦾 Eliza Daemon - Autonomous Agent for XMRT DAO

Main orchestration loop that runs Eliza's autonomous decision-making process.
Listen → Think → Act → Sleep cycle every 10 minutes.
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any

# Import task modules
from tasks.monitor_twitter import TwitterMonitor
from tasks.monitor_miners import MinerMonitor
from tasks.handle_rewards import RewardHandler
from tasks.governance_agent import GovernanceAgent
from tasks.notify_discord import DiscordNotifier

# Import AI brain
from agent.langchain_brain import ElizaAgent

# Import memory system
from memory.supabase_memory import SupabaseMemory

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class ElizaDaemon:
    """Main Eliza Daemon orchestrator"""

    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self._setup_logging()

        # Initialize components
        self.eliza_brain = ElizaAgent(self.config)
        self.memory = SupabaseMemory(self.config)

        # Initialize task modules
        self.twitter_monitor = TwitterMonitor(self.config)
        self.miner_monitor = MinerMonitor(self.config)
        self.reward_handler = RewardHandler(self.config)
        self.governance_agent = GovernanceAgent(self.config)
        self.discord_notifier = DiscordNotifier(self.config)

        self.loop_count = 0

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Config file {config_path} not found!")
            raise

    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = self.config.get("daemon", {}).get("log_level", "INFO")
        logging.basicConfig(
            filename="logs/eliza.log",
            level=getattr(logging, log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Also log to console
        console = logging.StreamHandler()
        console.setLevel(getattr(logging, log_level))
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

    async def listen_phase(self) -> Dict[str, Any]:
        """Phase 1: Listen to all event sources"""
        logging.info("👂 LISTEN: Gathering information from all sources...")

        # Gather data from all monitoring sources in parallel
        tasks = [
            self.twitter_monitor.check_new_activity(),
            self.miner_monitor.update_miner_stats(),
            self.governance_agent.check_new_proposals(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        gathered_data = {
            "timestamp": datetime.now().isoformat(),
            "twitter_activity": results[0] if not isinstance(results[0], Exception) else {},
            "miner_stats": results[1] if not isinstance(results[1], Exception) else {},
            "governance_activity": results[2] if not isinstance(results[2], Exception) else {},
        }

        logging.info(f"📊 Gathered data: {len(str(gathered_data))} chars of information")
        return gathered_data

    async def think_phase(self, gathered_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: Process information and make decisions"""
        logging.info("🧠 THINK: Eliza is analyzing and making decisions...")

        # Store current data in memory
        await self.memory.store_context("latest_data", gathered_data)

        # Get historical context
        historical_context = await self.memory.get_recent_context(limit=5)

        # Let Eliza's brain process everything and decide
        decisions = await self.eliza_brain.analyze_and_decide(
            current_data=gathered_data,
            historical_context=historical_context,
            loop_count=self.loop_count
        )

        logging.info(f"💭 Eliza made {len(decisions.get('actions', []))} decisions")
        return decisions

    async def act_phase(self, decisions: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Execute decisions and take actions"""
        logging.info("⚡ ACT: Executing Eliza's decisions...")

        actions_taken = []

        # Execute different types of actions
        if decisions.get("rewards"):
            result = await self.reward_handler.process_rewards(decisions["rewards"])
            actions_taken.append({"type": "rewards", "result": result})

        if decisions.get("governance"):
            result = await self.governance_agent.execute_governance_actions(decisions["governance"])
            actions_taken.append({"type": "governance", "result": result})

        if decisions.get("social"):
            result = await self.twitter_monitor.execute_social_actions(decisions["social"])
            actions_taken.append({"type": "social", "result": result})

        if decisions.get("notifications"):
            result = await self.discord_notifier.send_notifications(decisions["notifications"])
            actions_taken.append({"type": "notifications", "result": result})

        # Store actions taken
        action_summary = {
            "timestamp": datetime.now().isoformat(),
            "loop_count": self.loop_count,
            "actions_taken": actions_taken,
            "decisions": decisions
        }

        await self.memory.store_context("actions_taken", action_summary)

        logging.info(f"✅ Completed {len(actions_taken)} action types")
        return action_summary

    async def eliza_main_loop(self):
        """Main autonomous loop: Listen → Think → Act → Sleep"""
        loop_interval = self.config.get("daemon", {}).get("loop_interval_seconds", 600)

        logging.info("🦾 Eliza Daemon starting autonomous operation...")
        logging.info(f"⏰ Loop interval: {loop_interval} seconds ({loop_interval/60} minutes)")

        while True:
            try:
                self.loop_count += 1
                cycle_start = datetime.now()

                logging.info(f"\n🔄 === ELIZA CYCLE #{self.loop_count} STARTING ===")

                # Phase 1: Listen
                gathered_data = await self.listen_phase()

                # Phase 2: Think  
                decisions = await self.think_phase(gathered_data)

                # Phase 3: Act
                actions_summary = await self.act_phase(decisions)

                # Calculate cycle time
                cycle_duration = (datetime.now() - cycle_start).total_seconds()

                logging.info(f"✨ === CYCLE #{self.loop_count} COMPLETE ({cycle_duration:.1f}s) ===\n")

                # Phase 4: Sleep
                logging.info(f"💤 Eliza sleeping for {loop_interval} seconds...")
                await asyncio.sleep(loop_interval)

            except KeyboardInterrupt:
                logging.info("🛑 Eliza Daemon stopped by user")
                break
            except Exception as e:
                logging.error(f"❌ Error in main loop: {str(e)}")
                logging.error(f"🔄 Continuing after error...")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

async def main():
    """Entry point for Eliza Daemon"""
    daemon = ElizaDaemon()
    await daemon.eliza_main_loop()

if __name__ == "__main__":
    print("🦾 Starting Eliza Daemon...")
    asyncio.run(main())
