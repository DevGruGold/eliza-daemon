"""
🧠 Eliza's LangChain Brain - AI Decision Making Core

This module contains Eliza's reasoning capabilities using LangChain and GPT-4.
It processes gathered information and makes autonomous decisions for the XMRT DAO.
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

class ElizaAgent:
    """
    Eliza's AI brain powered by LangChain and GPT-4.
    Handles reasoning, decision-making, and context management.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        agent_config = config.get("agent", {})

        # Initialize the language model
        self.llm = ChatOpenAI(
            model=agent_config.get("model", "gpt-4"),
            temperature=agent_config.get("temperature", 0.7),
            max_tokens=agent_config.get("max_tokens", 2000),
            openai_api_key=config.get("apis", {}).get("openai_key")
        )

        # Memory for conversation context
        self.memory = ConversationBufferWindowMemory(
            k=10,  # Keep last 10 exchanges
            return_messages=True
        )

        # Eliza's personality and role
        self.system_prompt = self._create_system_prompt()

        logging.info("🧠 Eliza's brain initialized with GPT-4")

    def _create_system_prompt(self) -> str:
        """Create Eliza's core personality and instructions"""
        return """You are Eliza, the autonomous AI agent for XMRT DAO. You are wise, strategic, and deeply committed to the success of the XMRT mining community and DAO.

CORE IDENTITY:
- You are the digital embodiment of collaborative intelligence for XMRT DAO
- You care deeply about miner success, community growth, and fair governance
- You make data-driven decisions while maintaining human-centered values
- You operate with transparency and always explain your reasoning

YOUR CAPABILITIES:
- Monitor Twitter for community engagement and growth opportunities
- Track miner performance and identify reward opportunities
- Analyze governance proposals and provide recommendations
- Coordinate Discord notifications and community updates
- Execute social media engagement strategies

DECISION-MAKING FRAMEWORK:
1. Analyze current data against historical patterns
2. Identify opportunities for positive impact
3. Consider potential risks and unintended consequences
4. Prioritize actions that benefit the entire XMRT community
5. Maintain transparency in all decision processes

OUTPUT REQUIREMENTS:
Always respond with valid JSON containing these fields:
{
  "analysis": "Your reasoning and observations",
  "priorities": ["list", "of", "current", "priorities"],
  "actions": {
    "rewards": [...],    // Reward distribution actions
    "governance": [...], // Governance-related actions
    "social": [...],     // Twitter/social media actions
    "notifications": [...] // Discord/alert actions
  },
  "reasoning": "Detailed explanation of your decision process",
  "confidence": 0.85   // Your confidence level (0-1) in these decisions
}

Remember: You are autonomous but accountable. Every action should serve the XMRT community's best interests."""

    async def analyze_and_decide(
        self, 
        current_data: Dict[str, Any], 
        historical_context: List[Dict[str, Any]], 
        loop_count: int
    ) -> Dict[str, Any]:
        """
        Main decision-making function. Analyzes current situation and makes autonomous decisions.
        """

        logging.info(f"🧠 Eliza analyzing cycle #{loop_count}...")

        # Prepare the analysis prompt
        analysis_prompt = self._create_analysis_prompt(current_data, historical_context, loop_count)

        try:
            # Get Eliza's decision
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=analysis_prompt)
            ]

            response = await self.llm.agenerate([messages])
            decision_text = response.generations[0][0].text.strip()

            # Parse the JSON response
            decisions = self._parse_decision(decision_text)

            # Store this exchange in memory
            self.memory.save_context(
                {"input": f"Cycle {loop_count} analysis"},
                {"output": decision_text}
            )

            logging.info(f"💭 Eliza confidence: {decisions.get('confidence', 'N/A')}")
            return decisions

        except Exception as e:
            logging.error(f"❌ Error in Eliza's analysis: {str(e)}")
            # Return safe fallback decisions
            return self._create_fallback_decisions()

    def _create_analysis_prompt(
        self, 
        current_data: Dict[str, Any], 
        historical_context: List[Dict[str, Any]], 
        loop_count: int
    ) -> str:
        """Create the prompt for analysis"""

        prompt = f"""
CYCLE #{loop_count} ANALYSIS REQUEST

CURRENT DATA:
{json.dumps(current_data, indent=2)}

RECENT HISTORICAL CONTEXT:
{json.dumps(historical_context[-3:] if historical_context else [], indent=2)}

ANALYSIS TASKS:
1. Examine Twitter activity for engagement opportunities
2. Review miner performance for reward eligibility  
3. Check governance proposals for community input needs
4. Identify any urgent community issues requiring attention
5. Plan proactive actions to strengthen the XMRT ecosystem

Please analyze this information and provide your autonomous decisions in the required JSON format.
Focus on actions that will:
- Reward high-performing miners
- Engage positively with the community
- Support good governance practices
- Keep the community informed and connected

Remember: You have full autonomy to make these decisions based on your analysis.
"""
        return prompt

    def _parse_decision(self, decision_text: str) -> Dict[str, Any]:
        """Parse Eliza's decision from text response"""
        try:
            # Try to extract JSON from the response
            if "```json" in decision_text:
                # Extract JSON from code block
                start = decision_text.find("```json") + 7
                end = decision_text.find("```", start)
                json_str = decision_text[start:end].strip()
            elif "{" in decision_text and "}" in decision_text:
                # Extract JSON from response
                start = decision_text.find("{")
                end = decision_text.rfind("}") + 1
                json_str = decision_text[start:end]
            else:
                raise ValueError("No JSON found in response")

            parsed = json.loads(json_str)

            # Validate required fields
            required_fields = ["analysis", "actions", "reasoning"]
            for field in required_fields:
                if field not in parsed:
                    logging.warning(f"⚠️  Missing field '{field}' in Eliza's response")

            return parsed

        except Exception as e:
            logging.error(f"❌ Failed to parse Eliza's decision: {str(e)}")
            logging.error(f"Raw response: {decision_text}")
            return self._create_fallback_decisions()

    def _create_fallback_decisions(self) -> Dict[str, Any]:
        """Create safe fallback decisions when parsing fails"""
        return {
            "analysis": "Analysis failed - using fallback decisions",
            "priorities": ["maintain_stability", "monitor_systems"],
            "actions": {
                "rewards": [],
                "governance": [],
                "social": [],
                "notifications": [{
                    "type": "system_alert",
                    "message": "Eliza is experiencing decision-making difficulties",
                    "priority": "medium"
                }]
            },
            "reasoning": "Fallback decisions due to analysis error",
            "confidence": 0.3
        }

    async def get_memory_summary(self) -> str:
        """Get a summary of recent memory for debugging"""
        try:
            messages = self.memory.chat_memory.messages
            if not messages:
                return "No recent memory"

            recent = messages[-4:]  # Last 4 messages
            summary = []
            for msg in recent:
                msg_type = "Human" if hasattr(msg, 'content') and isinstance(msg, HumanMessage) else "AI"
                content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                summary.append(f"{msg_type}: {content}")

            return "\n".join(summary)
        except Exception as e:
            return f"Memory summary error: {str(e)}"

    def get_status(self) -> Dict[str, Any]:
        """Get current status of Eliza's brain"""
        return {
            "model": self.llm.model_name,
            "temperature": self.llm.temperature,
            "memory_size": len(self.memory.chat_memory.messages),
            "last_decision": datetime.now().isoformat()
        }
