from supabase import create_client, Client
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if url and key:
            self.supabase: Client = create_client(url, key)
            self.connected = True
        else:
            logger.warning("Supabase credentials not found, running in memory-only mode")
            self.connected = False
            self.local_memory = []

    async def store_decision(self, decision_data: dict):
        """Store Eliza's decision in persistent memory"""
        try:
            memory_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "decision_data": json.dumps(decision_data),
                "reasoning": decision_data.get("reasoning", ""),
                "actions_taken": len(decision_data.get("rewards", [])) + 
                              len(decision_data.get("proposals", [])) + 
                              len(decision_data.get("notifications", []))
            }

            if self.connected:
                result = self.supabase.table("eliza_memory").insert(memory_entry).execute()
                logger.info("💾 Decision stored in Supabase")
            else:
                self.local_memory.append(memory_entry)
                logger.info("💾 Decision stored locally")

        except Exception as e:
            logger.error(f"Memory storage error: {e}")

    async def recall_recent_decisions(self, limit: int = 10):
        """Recall recent decisions for context"""
        try:
            if self.connected:
                result = self.supabase.table("eliza_memory")\
                    .select("*")\
                    .order("timestamp", desc=True)\
                    .limit(limit)\
                    .execute()
                return result.data
            else:
                return self.local_memory[-limit:] if self.local_memory else []

        except Exception as e:
            logger.error(f"Memory recall error: {e}")
            return []

    async def get_memory_stats(self):
        """Get statistics about stored memories"""
        try:
            if self.connected:
                result = self.supabase.table("eliza_memory")\
                    .select("*", count="exact")\
                    .execute()
                return {"total_decisions": result.count}
            else:
                return {"total_decisions": len(self.local_memory)}

        except Exception as e:
            logger.error(f"Memory stats error: {e}")
            return {"total_decisions": 0}
