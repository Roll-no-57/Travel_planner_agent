import asyncio
import os
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from crewai.agent import Agent
from crewai.flow.flow import Flow, listen, start, router, or_
from langchain_google_genai import ChatGoogleGenerativeAI
from crewai import LLM as CrewLLM
from dotenv import load_dotenv

# Load environment variables from .env and normalize Google key name
load_dotenv()
_GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

# Import your existing tools (assuming they're available)
# from your_tools import (
#     get_activity_tool,
#     get_hotels_tool, 
#     get_weather_info,
#     get_search_results_tool,
#     get_image_search_results_tool
# )

# For demo purposes, I'll create mock tools - replace with your actual tools
class MockWeatherTool:
    def run(self, location):
        return f"Weather in {location}: Sunny, 25°C, Perfect for travel!"

class MockHotelTool:
    def run(self, location, checkin, checkout, guests):
        return [{"name": f"Grand Hotel {location}", "rating": 4.5, "price": 150}]

class MockActivityTool:
    def run(self, location, activity_type):
        return [{"name": f"Top Activity in {location}", "rating": 4.8, "duration": "2 hours"}]


# Initialize Gemini for CrewAI via LiteLLM provider
# Using CrewAI's LLM wrapper ensures provider is correctly inferred
gemini = CrewLLM(
    model="gemini/gemini-2.0-flash",
    api_key=_GOOGLE_API_KEY,
    temperature=0.7,
)

# Pydantic Models for Structured Responses
class Geocode(BaseModel):
    latitude: float = 0.0
    longitude: float = 0.0

class Travel(BaseModel):
    from_location: str = ""
    to: str = ""
    estimate_time: int = 0
    estimate_price: int = 0
    option: str = "flight"

class Price(BaseModel):
    amount: int = 0
    currency: str = "USD"

class Accommodation(BaseModel):
    name: str = ""
    description: str = ""
    address: str = ""
    geocode: Geocode = Geocode()
    rating: float = 0.0
    review_count: int = 0
    phone: str = ""
    amenities: List[str] = []
    price: Price = Price()
    guests: int = 0
    image_urls: List[str] = []
    booking_url: str = ""

class Activity(BaseModel):
    tag: str = ""
    title: str = ""
    description: str = ""
    minimum_duration: str = ""
    booking_url: str = ""
    address: str = ""
    NumberOfReview: int = 0
    Ratings: float = 0.0
    geocode: Geocode = Geocode()
    image_urls: List[str] = []

class Day(BaseModel):
    title: str = ""
    date: str = ""
    description: str = ""
    day_number: str = ""
    activities: List[Activity] = []

class City(BaseModel):
    travel: Travel = Travel()
    Accomodation: Accommodation = Accommodation()
    days: List[Day] = []

class Overview(BaseModel):
    start_location: str = ""
    destination_location: str = ""
    summary: str = ""
    duration_days: int = 0
    people_count: int = 0
    start_date: str = ""
    end_date: str = ""
    image_urls: List[str] = []
    Estimated_overall_cost: int = 0

class Itinerary(BaseModel):
    Cities: List[City] = []
    overview: Overview = Overview()

class ChatbotResponse(BaseModel):
    message: str
    intent: str
    sessionId: str
    timestamp: str
    itinerary: Itinerary = Itinerary()

# Flow State
class TravelChatbotState(BaseModel):
    user_query: str = ""
    conversation_history: List[Dict] = []
    intent: str = ""
    sessionId: str = ""
    
    # Travel requirements
    start_location: Optional[str] = None
    destination: Optional[str] = None
    duration_days: Optional[int] = None
    people_count: Optional[int] = None
    budget_range: Optional[str] = None
    start_date: Optional[str] = None
    
    # Response data
    response: ChatbotResponse = ChatbotResponse(
        message="",
        intent="",
        sessionId="",
        timestamp="",
        itinerary=Itinerary()
    )

class TravelChatbotFlow(Flow[TravelChatbotState]):
    
    @start()
    def initialize_chat(self) -> Dict[str, Any]:
        """Initialize the chatbot conversation"""
        print(f"Processing query: {self.state.user_query}")
        
        # Generate session ID if not provided
        if not self.state.sessionId:
            self.state.sessionId = str(uuid.uuid4())
            
        # Set timestamp
        timestamp = datetime.now().isoformat()
        self.state.response.timestamp = timestamp
        self.state.response.sessionId = self.state.sessionId
        
        return {"query": self.state.user_query}

    @listen(initialize_chat)
    async def analyze_intent(self, query_data) -> str:
        """Analyze user intent and route accordingly"""
        intent_analyzer = Agent(
            role="Intent Analysis Specialist",
            goal="Analyze user query and determine the correct intent for routing",
            backstory="You are an expert in understanding user intentions for travel-related queries. "
                     "You can identify whether users want weather info, are collecting requirements, "
                     "planning trips, or having general conversation.",
            tools=[],
            verbose=True,
            llm=gemini
        )
        
        analysis_prompt = f"""
        Analyze this user query and conversation history to determine intent:
        
        Query: {self.state.user_query}
        Conversation History: {self.state.conversation_history}
        
        Classify the intent as one of:
        1. weather_information - User asking about weather conditions
        2. requirement_collection - User providing/discussing trip requirements (location, dates, budget, etc.)
        3. trip_planning - User ready to plan with complete requirements 
        4. general_conversation - General chat or greetings
        
        Current requirements status:
        - Start location: {self.state.start_location}
        - Destination: {self.state.destination} 
        - Duration: {self.state.duration_days}
        - People: {self.state.people_count}
        - Budget: {self.state.budget_range}
        
        Return only the intent classification.
        """
        
        result = await intent_analyzer.kickoff_async(analysis_prompt)
        intent = result.raw.strip().lower()
        
        # Extract intent from response if it contains extra text
        if "weather_information" in intent:
            intent = "weather_information"
        elif "trip_planning" in intent:
            intent = "trip_planning"  
        elif "requirement_collection" in intent:
            intent = "requirement_collection"
        else:
            intent = "general_conversation"
            
        self.state.intent = intent
        self.state.response.intent = intent
        
        print(f"Detected intent: {intent}")
        return intent

    @router(analyze_intent)
    def route_intent(self) -> str:
        """Route based on analyzed intent"""
        return self.state.intent

    @listen(or_("general_conversation", "requirement_collection"))
    async def handle_general_and_requirements(self) -> Dict[str, Any]:
        """Handle general conversation and requirement collection"""
        general_agent = Agent(
            role="Travel Requirements Collector",
            goal="Collect travel requirements and provide helpful conversation",
            backstory="You are a friendly travel assistant who helps users provide "
                     "all necessary information for trip planning. You collect: "
                     "start location, destination, duration, group size, and budget.",
            tools=[],
            verbose=True,
            llm=gemini
        )
        
        requirements_prompt = f"""
        User Query: {self.state.user_query}
        Current Requirements:
        - Start location: {self.state.start_location or 'Not provided'}
        - Destination: {self.state.destination or 'Not provided'}
        - Duration: {self.state.duration_days or 'Not provided'} days
        - People count: {self.state.people_count or 'Not provided'}
        - Budget: {self.state.budget_range or 'Not provided'}
        
        Intent: {self.state.intent}
        
        Generate a helpful response that:
        1. Acknowledges their message
        2. Asks for missing requirements if intent is requirement_collection
        3. Provides general travel advice if intent is general_conversation
        4. Is conversational and friendly
        
        For successful trip planning, we need:
        - Start location
        - Destination  
        - Number of days
        - Group size (people count)
        - Budget range
        """
        
        result = await general_agent.kickoff_async(requirements_prompt)
        
        # Update response
        self.state.response.message = result.raw
        
        return {"message": result.raw}

    @listen("weather_information") 
    async def handle_weather_info(self) -> Dict[str, Any]:
        """Handle weather information requests"""
        weather_agent = Agent(
            role="Weather Information Specialist",
            goal="Provide weather information for travel destinations",
            backstory="You are a weather expert who provides accurate and helpful "
                     "weather information for travelers.",
            tools=[],  # Replace with your actual weather tool (must be a CrewAI BaseTool)
            verbose=True,
            llm=gemini
        )
        
        # Extract location from query or use destination
        location = self.state.destination or "the requested location"
        
        weather_prompt = f"""
        User is asking about weather for: {location}
        User Query: {self.state.user_query}
        
        Use the weather tool to get current weather information and provide a helpful response.
        """
        
        result = await weather_agent.kickoff_async(weather_prompt)
        
        # Update response
        self.state.response.message = result.raw
        
        return {"weather_info": result.raw}

    @listen("trip_planning")
    async def plan_trip(self) -> Dict[str, Any]:
        """Handle complete trip planning with full itinerary"""
        trip_planner = Agent(
            role="Senior Travel Planner",
            goal="Create comprehensive travel itineraries with cities, hotels, and activities",
            backstory="You are an experienced travel planner who creates detailed "
                     "itineraries including city recommendations, accommodations, and activities.",
            tools=[],
            verbose=True,
            llm=gemini
        )
        
        planning_prompt = f"""
        Create a detailed trip plan with the following requirements:
        - Start location: {self.state.start_location}
        - Destination: {self.state.destination}
        - Duration: {self.state.duration_days} days
        - People count: {self.state.people_count}
        - Budget: {self.state.budget_range}
        - User query: {self.state.user_query}
        
        Suggest cities to visit and provide a comprehensive travel plan.
        Include recommendations for transportation, timing, and key attractions.
        """
        
        result = await trip_planner.kickoff_async(planning_prompt)
        
        # For demo purposes, create a structured itinerary
        # In real implementation, you'd use the hotel and activity tools here
        await self._populate_itinerary_data()
        
        self.state.response.message = f"Here's your complete {self.state.duration_days}-day itinerary for {self.state.destination}! " + result.raw
        
        return {"trip_plan": result.raw}

    async def _populate_itinerary_data(self):
        """Populate the structured itinerary data"""
        # Create sample structured data - replace with actual tool calls
        
        # Overview
        self.state.response.itinerary.overview = Overview(
            start_location=self.state.start_location or "Your Location",
            destination_location=self.state.destination or "Destination",
            summary=f"Amazing {self.state.duration_days}-day trip to {self.state.destination}",
            duration_days=self.state.duration_days or 5,
            people_count=self.state.people_count or 2,
            start_date=self.state.start_date or datetime.now().strftime("%Y-%m-%d"),
            end_date=(datetime.now() + timedelta(days=self.state.duration_days or 5)).strftime("%Y-%m-%d"),
            image_urls=[f"https://example.com/images/{self.state.destination}.jpg"],
            Estimated_overall_cost=(self.state.duration_days or 5) * 200 * (self.state.people_count or 2)
        )
        
        # Create a sample city
        sample_city = City(
            travel=Travel(
                from_location=self.state.start_location or "Origin",
                to=self.state.destination or "Destination",
                estimate_time=3,
                estimate_price=500,
                option="flight"
            ),
            Accomodation=Accommodation(
                name=f"Grand Hotel {self.state.destination}",
                description="Luxury hotel in the heart of the city",
                address=f"123 Main St, {self.state.destination}",
                rating=4.5,
                review_count=1250,
                price=Price(amount=150, currency="USD"),
                guests=self.state.people_count or 2,
                amenities=["WiFi", "Pool", "Gym", "Restaurant"],
                image_urls=[f"https://example.com/hotel/{self.state.destination}.jpg"]
            ),
            days=[]
        )
        
        # Create sample days with activities
        for day in range(1, (self.state.duration_days or 5) + 1):
            day_date = (datetime.now() + timedelta(days=day-1)).strftime("%Y-%m-%d")
            
            sample_day = Day(
                title=f"Day {day} - Explore {self.state.destination}",
                date=day_date,
                description=f"Full day of activities in {self.state.destination}",
                day_number=f"Day {day}",
                activities=[
                    Activity(
                        tag="sightseeing",
                        title=f"Top Attraction in {self.state.destination}",
                        description="Must-visit landmark with stunning views",
                        minimum_duration="2 hours",
                        address=f"456 Tourist St, {self.state.destination}",
                        Ratings=4.7,
                        NumberOfReview=892,
                        image_urls=[f"https://example.com/activity/{self.state.destination}_{day}.jpg"]
                    )
                ]
            )
            sample_city.days.append(sample_day)
        
        self.state.response.itinerary.Cities = [sample_city]

    @listen(or_(handle_general_and_requirements, handle_weather_info, plan_trip))
    def finalize_response(self, result) -> ChatbotResponse:
        """Finalize and return the chatbot response"""
        print(f"Final response intent: {self.state.response.intent}")
        print(f"Final response message: {self.state.response.message}")
        
        return self.state.response

# Usage function
async def process_travel_query(query: str, conversation_history: List[Dict] = None, session_id: str = None):
    """Process a travel query and return structured response"""
    
    flow = TravelChatbotFlow()
    
    # Set initial state
    inputs = {
        "user_query": query,
        "conversation_history": conversation_history or [],
        "sessionId": session_id or str(uuid.uuid4())
    }
    
    # For demo, extract some requirements from query if present
    if "days" in query.lower() or "day" in query.lower():
        try:
            import re
            days_match = re.search(r'(\d+)\s*days?', query.lower())
            if days_match:
                inputs["duration_days"] = int(days_match.group(1))
        except:
            pass
    
    if "people" in query.lower() or "person" in query.lower():
        try:
            import re
            people_match = re.search(r'(\d+)\s*(?:people|person)', query.lower()) 
            if people_match:
                inputs["people_count"] = int(people_match.group(1))
        except:
            pass
    
    flow.plot("TravelChatbotFlow")
    result = await flow.kickoff_async(inputs=inputs)
    
    return result

# Example usage
if __name__ == "__main__":
    async def test_chatbot():
        # Test different types of queries
        
        # General greeting
        print("=== Testing General Conversation ===")
        result1 = await process_travel_query("Hello! I want to plan a trip")
        print(f"Response: {result1.message}")
        print(f"Intent: {result1.intent}\n")
        
        # # Requirement collection  
        # print("=== Testing Requirement Collection ===")
        # result2 = await process_travel_query("I want to visit Paris for 5 days with 2 people")
        # print(f"Response: {result2.message}")
        # print(f"Intent: {result2.intent}\n")
        
        # # Weather query
        # print("=== Testing Weather Information ===")
        # result3 = await process_travel_query("What's the weather like in Tokyo?")
        # print(f"Response: {result3.message}")
        # print(f"Intent: {result3.intent}\n")
        
        # # Trip planning (with complete requirements)
        # print("=== Testing Trip Planning ===")
        # result4 = await process_travel_query("Plan a 5-day trip to Paris for 2 people from New York with a $2000 budget")
        # print(f"Response: {result4.message}")
        # print(f"Intent: {result4.intent}")
        # print(f"Cities in itinerary: {len(result4.itinerary.Cities)}")
        # if result4.itinerary.Cities:
        #     print(f"Hotel: {result4.itinerary.Cities[0].Accomodation.name}")
        #     print(f"Days planned: {len(result4.itinerary.Cities[0].days)}")
    
    asyncio.run(test_chatbot())
