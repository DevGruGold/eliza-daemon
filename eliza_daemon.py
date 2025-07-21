import asyncio
import logging
import json
from datetime import datetime
from tasks.monitor_twitter import check_new_followers
from tasks.monitor_miners import update_miner_stats
from tasks.handle_rewards import distribute_rewards
from tasks.governance_agent import review_proposals
from tasks.notify_discord import send_notification
from agent.langchain_brain import ElizaAgent
from memory.supabase_memory import MemoryManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/eliza.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ElizaDaemon:
    def __init__(self):
        self.eliza = ElizaAgent()
        self.memory = MemoryManager()
        self.running = True
        logger.info("🦾 Eliza Daemon initialized")

    async def eliza_loop(self):
        """Main autonomous loop - Listen → Think → Act → Sleep"""
        while self.running:
            try:
                logger.info("🔁 Eliza Daemon waking up...")

                # LISTEN - Gather data from all sources
                logger.info("👂 Listening for events...")
                new_followers = await check_new_followers()
                miner_stats = await update_miner_stats()

                # THINK - Process with AI brain
                logger.info("🧠 Eliza is thinking...")
                self.eliza.remember(miner_stats)
                decisions = await self.eliza.decide(new_followers, miner_stats)

                # ACT - Execute decisions
                logger.info("⚡ Taking actions...")
                if decisions.get("rewards"):
                    await distribute_rewards(decisions["rewards"])

                if decisions.get("proposals"):
                    await review_proposals(decisions["proposals"])

                if decisions.get("notifications"):
                    await send_notification(decisions["notifications"])

                # Store memory
                await self.memory.store_decision(decisions)

                logger.info("💤 Eliza Daemon sleeping for 10 minutes...")
                await asyncio.sleep(600)  # 10 minute loop

            except Exception as e:
                logger.error(f"❌ Error in Eliza loop: {e}")
                await asyncio.sleep(60)  # Short sleep on error

    async def start(self):
        """Start the daemon"""
        logger.info("🚀 Starting Eliza Daemon...")
        await send_notification("🦾 Eliza Daemon is now online and autonomous!")
        await self.eliza_loop()

    def stop(self):
        """Stop the daemon gracefully"""
        logger.info("🛑 Stopping Eliza Daemon...")
        self.running = False

if __name__ == "__main__":
    daemon = ElizaDaemon()
    try:
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        daemon.stop()
        logger.info("👋 Eliza Daemon shutdown complete")
