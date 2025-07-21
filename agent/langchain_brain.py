from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
import json
import os
from dotenv import load_dotenv

load_dotenv()

class ElizaAgent:
    def __init__(self):
        self.memory = ConversationBufferMemory(return_messages=True)
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_KEY")
        )

        # Tools for Eliza to use
        self.tools = [
            Tool(
                name="calculate_rewards",
                description="Calculate mining rewards based on performance",
                func=self._calculate_rewards
            ),
            Tool(
                name="analyze_sentiment",
                description="Analyze sentiment of community interactions",
                func=self._analyze_sentiment
            )
        ]

        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent="conversational-react-description",
            memory=self.memory,
            verbose=True
        )

    def remember(self, data):
        """Store information in Eliza's memory"""
        context = f"Latest data update: {json.dumps(data, indent=2)}"
        self.memory.save_context(
            {"input": "system_update"}, 
            {"output": context}
        )

    async def decide(self, followers, miners):
        """Make autonomous decisions based on input data"""

        prompt = f"""
        As Eliza, the autonomous agent for XMRT DAO, analyze this data and decide actions:

        NEW FOLLOWERS: {json.dumps(followers, indent=2)}
        MINER STATS: {json.dumps(miners, indent=2)}

        Based on this information, what actions should I take? Consider:
        - Should I reward high-performing miners?
        - Are there governance proposals to review?
        - Should I engage with new community members?
        - Any Discord notifications needed?

        Return your decision as JSON with these keys:
        - "rewards": [list of reward actions]
        - "proposals": [list of governance actions]  
        - "notifications": [list of notification messages]
        - "reasoning": "explanation of decisions"
        """

        try:
            response = self.agent.run(prompt)
            # Try to parse as JSON, fallback to structured response
            if response.startswith('{'):
                return json.loads(response)
            else:
                return {
                    "rewards": [],
                    "proposals": [],
                    "notifications": [response],
                    "reasoning": "Generated narrative response"
                }
        except Exception as e:
            return {
                "rewards": [],
                "proposals": [],
                "notifications": [f"Error in decision making: {e}"],
                "reasoning": "Error occurred during processing"
            }

    def _calculate_rewards(self, performance_data):
        """Calculate mining rewards based on performance"""
        # Implement reward calculation logic
        return "Rewards calculated based on mining performance"

    def _analyze_sentiment(self, text):
        """Analyze sentiment of community interactions"""
        # Implement sentiment analysis
        return "Sentiment analysis complete"
