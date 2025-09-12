import asyncio
import os
from typing import Any, Dict, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from crewai.agent import Agent
from crewai.flow.flow import Flow, listen, start
from crewai import LLM as CrewLLM
from dotenv import load_dotenv

# Load env
load_dotenv()
_GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

gemini = CrewLLM(
    model="gemini/gemini-1.5-flash",
    api_key=_GOOGLE_API_KEY,
    temperature=0.7,
)

# ---------- Schema Models ----------
class Geocode(BaseModel):
    latitude: float = 0.0
    longitude: float = 0.0

class Price(BaseModel):
    amount: float = 0.0
    currency: str = "USD"

class Activity(BaseModel):
    tag: str = "general"
    title: str = "activity name"
    description: str = "activity description"
    minimum_duration: str = "1 hour"
    booking_url: str = ""
    address: str = ""
    NumberOfReview: int = 0
    Ratings: float = 0.0
    geocode: Geocode = Geocode()
    image_urls: List[str] = []

class DayPlan(BaseModel):
    title: str = "Day 1"
    date: str = "YYYY-MM-DD"
    description: str = "Day description"
    day_number: str = "Day 1"
    activities: List[Activity] = []

class Accommodation(BaseModel):
    name: str = "hotel name"
    description: str = "hotel description"
    address: str = "hotel address"
    geocode: Geocode = Geocode()
    rating: float = 0.0
    review_count: int = 0
    phone: str = ""
    amenities: List[str] = []
    price: Price = Price()
    guests: int = 0
    image_urls: List[str] = []
    booking_url: str = ""

class Travel(BaseModel):
    from_: str = Field("departure location", alias="from")
    to: str = "arrival city"
    estimate_time: int = 0
    estimate_price: int = 0
    option: str = "flight/train/bus/car"

    class Config:
        populate_by_name = True  # allow both "from" and "from_"

class CityPlan(BaseModel):
    travel: Travel
    Accomodation: Accommodation
    days: List[DayPlan]

class Overview(BaseModel):
    start_location: str = "departure city"
    destination_location: str = "Multiple Cities"
    summary: str = "trip summary"
    duration_days: int = 0
    people_count: int = 0
    start_date: str = "YYYY-MM-DD"
    end_date: str = "YYYY-MM-DD"
    image_urls: List[str] = []
    Estimated_overall_cost: int = 0

class Itinerary(BaseModel):
    Cities: List[CityPlan]
    overview: Overview

class TripPlan(BaseModel):
    itinerary: Itinerary
    message: str
    intent: str
    sessionId: str
    timestamp: str

# ---------- Flow State ----------
class TripPlannerState(BaseModel):
    cities: List[CityPlan] | None = None
    overview: Overview | None = None
    final_plan: TripPlan | None = None

# ---------- Flow ----------
class TripPlannerFlow(Flow[TripPlannerState]):

    @start()
    def initialize_trip(self) -> Dict[str, Any]:
        return {"sessionId": "session-123"}

    @listen(initialize_trip)
    async def select_cities(self, sessionId: str) -> Dict[str, Any]:
        agent = Agent(
            role="City Selector",
            goal="Choose cities with travel info, hotel, and daily plans",
            backstory="Expert in designing detailed travel city plans.",
            tools=[],
            verbose=False,
            llm=gemini,
        )
        query = """
        Create 1 CityPlan JSON with:
        - travel (with "from" and "to")
        - Accomodation
        - 1 day with 1 activity
        Follow the exact schema strictly.
        """
        result = await agent.kickoff_async(query, response_format=CityPlan)

        if result.pydantic:
            self.state.cities = [result.pydantic]
        else:
            # fallback dummy if parsing fails
            self.state.cities = [CityPlan(
                travel=Travel(),
                Accomodation=Accommodation(),
                days=[DayPlan(activities=[Activity()])]
            )]

        return {"cities": self.state.cities}

    @listen(select_cities)
    async def generate_overview(self, cities: List[CityPlan]) -> Dict[str, Any]:
        agent = Agent(
            role="Overview Generator",
            goal="Create the trip overview",
            backstory="Expert in summarizing travel itineraries.",
            tools=[],
            verbose=False,
            llm=gemini,
        )
        query = "Generate the overview JSON following schema."
        result = await agent.kickoff_async(query, response_format=Overview)
        self.state.overview = result.pydantic or Overview()
        return {"overview": self.state.overview}

    @listen(generate_overview)
    def finalize_plan(self, overview: Overview) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()

        itinerary = Itinerary(
            Cities=self.state.cities or [],
            overview=self.state.overview or Overview(),
        )

        trip_plan = TripPlan(
            itinerary=itinerary,
            message="Here’s your planned trip!",
            intent="trip_planning",
            sessionId="session-123",
            timestamp=now,
        )

        self.state.final_plan = trip_plan
        print(trip_plan.model_dump_json(indent=2, by_alias=True))
        return {"final_plan": trip_plan}

# ---------- Run ----------
async def run_flow():
    flow = TripPlannerFlow()
    result = await flow.kickoff_async(inputs={})
    return result

if __name__ == "__main__":
    asyncio.run(run_flow())
