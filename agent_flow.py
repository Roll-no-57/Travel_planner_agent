import asyncio
import os
from typing import Any, Dict, List

from pydantic import BaseModel
from crewai.agent import Agent
from crewai.flow.flow import Flow, listen, start
from crewai import LLM as CrewLLM
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
_GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

# LLM setup
gemini = CrewLLM(
    model="gemini/gemini-1.5-flash",
    api_key=_GOOGLE_API_KEY,
    temperature=0.7,
)

# ---------- Structured Data ----------
class MarketAnalysis(BaseModel):
    key_trends: List[str]
    market_size: str
    competitors: List[str]

class MarketResearchState(BaseModel):
    product: str = ""
    key_trends: List[str] | None = None
    market_size: str | None = None
    competitors: List[str] | None = None
    analysis: MarketAnalysis | None = None

# Sub-models for agent responses
class TrendsOutput(BaseModel):
    key_trends: List[str]

class MarketSizeOutput(BaseModel):
    market_size: str

class CompetitorsOutput(BaseModel):
    competitors: List[str]

# ---------- Flow ----------
class MarketResearchFlow(Flow[MarketResearchState]):

    @start()
    def initialize_research(self) -> Dict[str, Any]:
        return {"product": self.state.product}

    @listen(initialize_research)
    async def analyze_trends(self, product: str) -> Dict[str, Any]:
        agent = Agent(
            role="Trend Analyst",
            goal=f"Find market trends for {product}",
            backstory="You are an expert in identifying emerging and ongoing trends.",
            tools=[],
            verbose=False,
            llm=gemini,
        )
        query = f"List 5-7 key market trends for {product}."
        result = await agent.kickoff_async(query, response_format=TrendsOutput)
        

        # ✅ save to state
        self.state.key_trends = result.pydantic.key_trends
        return {"key_trends": result.pydantic.key_trends}

    @listen(analyze_trends)
    async def analyze_size(self, key_trends: List[str]) -> Dict[str, Any]:
        agent = Agent(
            role="Market Size Analyst",
            goal=f"Estimate the market size for {self.state.product}",
            backstory="You are a skilled financial analyst estimating market size.",
            tools=[],
            verbose=False,
            llm=gemini,
        )
        query = f"Based on the following trends: {key_trends}, estimate the current market size for {self.state.product}."
        result = await agent.kickoff_async(query, response_format=MarketSizeOutput)

        # ✅ save to state
        self.state.market_size = result.pydantic.market_size
        return {"market_size": result.pydantic.market_size}

    @listen(analyze_size)
    async def analyze_competitors(self, market_size: str) -> Dict[str, Any]:
        agent = Agent(
            role="Competitor Analyst",
            goal=f"Identify main competitors for {self.state.product}",
            backstory="You are a business strategist specializing in competitive analysis.",
            tools=[],
            verbose=False,
            llm=gemini,
        )
        query = f"Given the market size: {market_size}, list the top 5 major competitors in {self.state.product} market."
        result = await agent.kickoff_async(query, response_format=CompetitorsOutput)

        # ✅ save to state
        self.state.competitors = result.pydantic.competitors
        return {"competitors": result.pydantic.competitors}

    @listen(analyze_competitors)
    def finalize_analysis(self, competitors) -> Dict[str, Any]:
        analysis = MarketAnalysis(
            key_trends=self.state.key_trends or [],
            market_size=self.state.market_size or "Unknown",
            competitors=self.state.competitors or [],
        )
        # ✅ only output final JSON
        print(analysis.model_dump_json(indent=2))
        return {"analysis": analysis}

# ---------- Run ----------
async def run_flow():
    flow = MarketResearchFlow()
    result = await flow.kickoff_async(inputs={"product": "AI-powered chatbots"})
    return result

if __name__ == "__main__":
    asyncio.run(run_flow())
