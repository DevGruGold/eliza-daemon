"""
🦾 Eliza Daemon - Main Orchestration Loop

Autonomous AI agent that continuously monitors, reasons, and acts for XMRT DAO.
Runs in 10-minute cycles: Listen → Think → Act → Sleep
"""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

# Import task modules
from tasks.monitor_twitter import check_new_followers, engage_with_community
from tasks.monitor_miners import update_miner_stats, check_miner_alerts
from tasks.handle_rewards import distribute_rewards, calculate_rewards
from tasks.governance_agent import review_proposals, create_proposals
from tasks.notify_discord import send_discord_alert

# Import AI brain
from agent.langchain_brain import ElizaAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/eliza.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ElizaDaemon')

class ElizaDaemon:
    def __init__(self):
        """Initialize Eliza with AI brain and configuration"""
        logger.info("🦾 Initializing Eliza Daemon...")

        # Load configuration
        self.config = self.load_config()

        # Initialize AI brain
        self.eliza = ElizaAgent(self.config)

        # Daemon state
        self.running = True
        self.cycle_count = 0

        logger.info("✅ Eliza Daemon initialized successfully!")

    def load_config(self):
        """Load configuration from config.json"""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("❌ config.json not found! Please copy from config.json.template")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in config.json: {e}")
            raise

    async def listen_phase(self):
        """Listen: Gather data from all monitoring sources"""
        logger.info("👂 LISTEN: Gathering data from all sources...")

        # Gather data concurrently
        tasks = [
            check_new_followers(),
            update_miner_stats(),
            # Add more monitoring tasks as needed
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        data = {
            'new_followers': results[0] if not isinstance(results[0], Exception) else [],
            'miner_stats': results[1] if not isinstance(results[1], Exception) else {},
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"📊 Data collected: {len(data.get('new_followers', []))} new followers, miner stats updated")
        return data

    async def think_phase(self, data):
        """Think: Use AI brain to analyze data and decide actions"""
        logger.info("🧠 THINK: Analyzing data and making decisions...")

        # Store data in memory
        self.eliza.remember(data)

        # Get AI-powered decisions
        decisions = await self.eliza.decide(data)

        logger.info(f"💭 Decisions made: {list(decisions.keys())}")
        return decisions

    async def act_phase(self, decisions):
        """Act: Execute the decisions made by AI brain"""
        logger.info("⚡ ACT: Executing decisions...")

        # Execute actions concurrently where possible
        action_tasks = []

        # Handle rewards
        if 'rewards' in decisions and decisions['rewards']:
            action_tasks.append(distribute_rewards(decisions['rewards']))

        # Handle proposals
        if 'proposals' in decisions and decisions['proposals']:
            action_tasks.append(create_proposals(decisions['proposals']))

        # Handle community engagement
        if 'tweets' in decisions and decisions['tweets']:
            action_tasks.append(engage_with_community(decisions['tweets']))

        # Handle alerts
        if 'alerts' in decisions and decisions['alerts']:
            action_tasks.append(send_discord_alert(decisions['alerts']))

        # Execute all actions
        if action_tasks:
            results = await asyncio.gather(*action_tasks, return_exceptions=True)
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            logger.info(f"✅ {success_count}/{len(action_tasks)} actions completed successfully")
        else:
            logger.info("😴 No actions required this cycle")

    async def eliza_cycle(self):
        """Complete Eliza decision cycle: Listen → Think → Act"""
        self.cycle_count += 1
        logger.info(f"🔄 Starting Eliza Cycle #{self.cycle_count}")

        try:
            # Listen: Gather data
            data = await self.listen_phase()

            # Think: Make decisions
            decisions = await self.think_phase(data)

            # Act: Execute decisions
            await self.act_phase(decisions)

            logger.info(f"✅ Cycle #{self.cycle_count} completed successfully")

        except Exception as e:
            logger.error(f"❌ Error in cycle #{self.cycle_count}: {e}")
            await send_discord_alert({
                'type': 'error',
                'message': f"Eliza Daemon error in cycle #{self.cycle_count}: {str(e)}"
            })

    async def run(self):
        """Main daemon loop - runs continuously"""
        logger.info("🚀 Eliza Daemon starting main loop...")

        while self.running:
            try:
                await self.eliza_cycle()

                # Sleep for 10 minutes between cycles
                logger.info("💤 Eliza sleeping for 10 minutes...")
                await asyncio.sleep(600)  # 10 minutes

            except KeyboardInterrupt:
                logger.info("⏹️ Shutdown signal received")
                self.running = False
            except Exception as e:
                logger.error(f"❌ Unexpected error in main loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

        logger.info("👋 Eliza Daemon shutdown complete")

    def stop(self):
        """Gracefully stop the daemon"""
        logger.info("🛑 Stopping Eliza Daemon...")
        self.running = False

async def main():
    """Entry point for Eliza Daemon"""
    eliza = ElizaDaemon()

    # Handle graceful shutdown
    import signal
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        eliza.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the daemon
    await eliza.run()

if __name__ == "__main__":
    asyncio.run(main())
