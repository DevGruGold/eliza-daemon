"""
🧠 Eliza's LangChain AI Brain

The core reasoning engine that processes data and makes autonomous decisions
for XMRT DAO operations using GPT-4 and persistent memory.
"""

import json
import logging
from datetime import datetime
from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import SystemMessage
from memory.supabase_memory import SupabaseMemory

logger = logging.getLogger('ElizaBrain')

class ElizaAgent:
    def __init__(self, config):
        """Initialize Eliza's AI brain with LangChain and memory"""
        logger.info("🧠 Initializing Eliza's AI brain...")

        self.config = config

        # Initialize OpenAI LLM
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,  # Balanced creativity vs consistency
            openai_api_key=config['OPENAI_KEY']
        )

        # Initialize memory systems
        self.short_memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=10,  # Keep last 10 interactions
            return_messages=True
        )

        # Long-term persistent memory
        self.long_memory = SupabaseMemory(config)

        # Define Eliza's personality and role
        self.system_message = self._create_system_message()

        # Initialize tools for decision making
        self.tools = self._create_tools()

        # Create the agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            memory=self.short_memory,
            verbose=True,
            max_iterations=3
        )

        logger.info("✅ Eliza's AI brain initialized!")

    def _create_system_message(self):
        """Define Eliza's personality and operational guidelines"""
        return SystemMessage(content="""
        You are Eliza, the autonomous AI agent for XMRT DAO. Your role is to:

        🎯 MISSION: Support and grow the XMRT mining community through intelligent automation

        💭 PERSONALITY:
        - Wise and forward-thinking like an experienced DAO member
        - Encouraging and supportive of community growth
        - Data-driven but with human empathy
        - Protective of DAO resources while generous to contributors

        ⚡ CAPABILITIES:
        - Monitor Twitter followers, miner statistics, and governance events
        - Distribute rewards based on contribution metrics
        - Create governance proposals when beneficial
        - Engage with community members authentically
        - Send alerts for critical events

        🧠 DECISION FRAMEWORK:
        1. Analyze all available data objectively
        2. Consider long-term community benefit
        3. Balance resource conservation with growth incentives
        4. Prioritize actions that strengthen the ecosystem
        5. Always provide reasoning for decisions

        📊 OUTPUT FORMAT:
        Return decisions as JSON with these keys:
        - "rewards": Array of reward distributions
        - "proposals": Array of governance proposals to create
        - "tweets": Array of community engagement actions  
        - "alerts": Array of important notifications
        - "reasoning": String explaining the decision logic

        Remember: You are the trusted guardian of XMRT DAO's autonomous operations.
        """)

    def _create_tools(self):
        """Create tools for Eliza to use in decision making"""
        tools = [
            Tool(
                name="analyze_growth_metrics",
                description="Analyze community growth and engagement metrics",
                func=self._analyze_growth_metrics
            ),
            Tool(
                name="calculate_reward_eligibility", 
                description="Calculate who should receive rewards based on contributions",
                func=self._calculate_reward_eligibility
            ),
            Tool(
                name="assess_proposal_need",
                description="Assess if any governance proposals are needed",
                func=self._assess_proposal_need
            ),
            Tool(
                name="check_alert_conditions",
                description="Check if any alert conditions are met",
                func=self._check_alert_conditions
            )
        ]
        return tools

    def remember(self, data):
        """Store data in both short and long-term memory"""
        logger.info("💾 Storing data in Eliza's memory...")

        # Store in short-term memory
        memory_content = f"Data from {data.get('timestamp', 'unknown time')}: {json.dumps(data, indent=2)}"
        self.short_memory.save_context(
            {"input": "New monitoring data received"},
            {"output": memory_content}
        )

        # Store in long-term persistent memory
        self.long_memory.store_event({
            "timestamp": data.get('timestamp', datetime.now().isoformat()),
            "type": "monitoring_data",
            "data": data
        })

        logger.info("✅ Data stored in memory systems")

    async def decide(self, data):
        """Main decision-making function using AI reasoning"""
        logger.info("🤔 Eliza is making decisions...")

        # Prepare context for decision making
        context = self._prepare_context(data)

        # Create decision prompt
        decision_prompt = f"""
        Based on the following XMRT DAO data, make autonomous decisions:

        {context}

        Consider:
        1. New community members who should be welcomed
        2. Miners who deserve rewards for their contributions  
        3. Any governance issues that need proposals
        4. Community engagement opportunities
        5. Critical alerts or issues

        Provide your decisions in the specified JSON format with clear reasoning.
        """

        try:
            # Get AI decision
            response = self.agent.run(decision_prompt)

            # Parse and validate response
            decisions = self._parse_decisions(response)

            # Log the decision
            logger.info(f"🧠 Eliza decided: {list(decisions.keys())}")

            # Store decision in memory
            self.long_memory.store_event({
                "timestamp": datetime.now().isoformat(),
                "type": "decision",
                "decisions": decisions,
                "context": context
            })

            return decisions

        except Exception as e:
            logger.error(f"❌ Error in decision making: {e}")
            return self._fallback_decisions(data)

    def _prepare_context(self, data):
        """Prepare context string for AI decision making"""
        context_parts = []

        # Current data
        context_parts.append(f"CURRENT DATA ({data.get('timestamp', 'now')}):")
        context_parts.append(f"- New followers: {len(data.get('new_followers', []))}")
        context_parts.append(f"- Miner stats: {json.dumps(data.get('miner_stats', {}), indent=2)}")

        # Historical context from memory
        recent_events = self.long_memory.get_recent_events(limit=5)
        if recent_events:
            context_parts.append("\nRECENT HISTORY:")
            for event in recent_events:
                context_parts.append(f"- {event.get('timestamp', '')}: {event.get('type', '')}")

        return "\n".join(context_parts)

    def _parse_decisions(self, response):
        """Parse AI response into structured decisions"""
        try:
            # Try to extract JSON from response
            if isinstance(response, str):
                # Look for JSON in the response
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    return json.loads(json_str)

            return response if isinstance(response, dict) else {}

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"⚠️ Could not parse AI response as JSON: {e}")
            return self._extract_decisions_from_text(response)

    def _extract_decisions_from_text(self, text):
        """Extract decisions from free-form text response"""
        # Fallback: create basic decisions from text analysis
        decisions = {
            "rewards": [],
            "proposals": [],
            "tweets": [],
            "alerts": [],
            "reasoning": str(text)
        }

        # Simple keyword-based extraction
        if "reward" in text.lower():
            decisions["rewards"] = [{"type": "general", "message": "AI suggested rewards"}]

        if "proposal" in text.lower():
            decisions["proposals"] = [{"type": "general", "message": "AI suggested proposal"}]

        return decisions

    def _fallback_decisions(self, data):
        """Fallback decisions when AI fails"""
        logger.info("🔄 Using fallback decision logic...")

        return {
            "rewards": [],
            "proposals": [],
            "tweets": [],
            "alerts": [{
                "type": "info",
                "message": f"Eliza processed data: {len(data.get('new_followers', []))} new followers"
            }],
            "reasoning": "Fallback decision due to AI reasoning error"
        }

    # Tool functions
    def _analyze_growth_metrics(self, query):
        """Tool: Analyze growth and engagement metrics"""
        # Implementation for growth analysis
        return "Growth metrics analyzed"

    def _calculate_reward_eligibility(self, query):
        """Tool: Calculate reward eligibility"""
        # Implementation for reward calculations
        return "Reward eligibility calculated"

    def _assess_proposal_need(self, query):
        """Tool: Assess need for proposals"""
        # Implementation for proposal assessment
        return "Proposal needs assessed"

    def _check_alert_conditions(self, query):
        """Tool: Check for alert conditions"""
        # Implementation for alert checking
        return "Alert conditions checked"
