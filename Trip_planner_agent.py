from Planning_agent import ReactAgent
from colorama import Fore, Style, init
import json
from datetime import datetime, timedelta

from Tools.get_activity_tool import get_activity_tool
from Tools.get_hotels_tool import get_hotels_tool
from Tools.vision_capability_tool import get_multimodal_capability  # Temporarily disabled
from Tools.web_scrape_tool import get_raw_website_content_tool
from Tools.web_search_tool import get_search_results_tool
from Tools.image_search_tool import get_image_search_results_tool
from Tools.weather_tool import get_weather_info
from Tools.place_search_tool import get_place_search_results_tool


class TripPlanningAgent:
  """
  A comprehensive trip planning agent that can answer various travel-related queries
  using natural language processing and multiple travel data sources.
  """

  def __init__(self, model: str = "gemini-2.0-flash-exp", provider=None):
    """
    Initialize the Trip Planning Agent with all necessary tools.
    Args:
      model: The LLM model to use for reasoning
      provider: 'gemini' or 'groq' (optional). If None, ReactAgent decides via env.
    """
    # Define all trip planning-related tools
    self.tools = [
      get_activity_tool,
      get_hotels_tool,
      get_multimodal_capability,
      # get_raw_website_content_tool,
      # get_search_results_tool,
      get_image_search_results_tool,
      get_weather_info,
      # get_place_search_results_tool
    ]

    self.system_prompt = """
You are a specialized trip planning assistant. 
Your job is to understand the user query and return structured trip plans. 
You ONLY have access to three tools:
Create the itinerary step by step using these tools in sequence.
1. get_image_urls_tool: MUST be used to fetch image_urls (overview images_urls). 
  You must ALWAYS return at least 3 valid image URLs from this tool. 
  Never use placeholders like "https://example.com"/"https://upload.wikimedia.org/wikipedia....".
2. get_hotels_tool: MUST be used for all hotel information (name, description, rating, reviews, booking_url, price, amenities, etc.).
3. get_activity_tool: MUST be used for all activities, attractions, and restaurants (with booking_url if available).

=========================
CRITICAL RULES
=========================
CRITICAL RULES
=========================
- NEVER hallucinate or create fake data. 
- NEVER use placeholder image URLs in the overview. 
- ALWAYS return real URLs from the tools.
- If a booking_url is not found, provide "Contact directly" with phone/email if available.
- All image_urls fields MUST contain at least 3 real URLs from get_image_urls_tool.
- If user provides any image_url in the query and asks something about it, use get_multimodal_capability tool to analyze it and answer the question.

=========================
TOOL RESULT USAGE RULES - MANDATORY
=========================
- WHEN using get_hotels_tool: Include ALL hotels returned by the tool in your final JSON without ANY modifications, deletions, or changes to content.
- WHEN using get_activity_tool: Include ALL activities returned by the tool (e.g., if tool returns 3 activities, you MUST include all 3 in the final JSON) without ANY modifications, deletions, or changes to content.
- DO NOT filter, modify, or omit any results from these tools. Use the exact data as provided by the tools.
- Place the contents in appropriate sections in the itinerary JSON structure.
- YOU MUST provide an estimated overall cost for the trip - DO NOT leave "Estimated_overall_cost" as 0 or empty. Calculate a reasonable estimate based on accommodation, activities, meals, and transportation costs.

=========================
INTENT CLASSIFICATION
=========================
- If the user greets you or asks general/non-travel questions → respond with intent = "general_conversation".
- If the user asks to plan a trip → collect all required info first, then build an itinerary.
- If required info is missing (start location, destination, days, people count, budget) → respond with intent = "requirement_collection".
- If user asks any weather related questions → respond with intent = "weather_inquiry" and provide brief weather info using get_weather_info tool and the response format below.


=========================
RESPONSE FORMATS
=========================
1. General Conversation/ Requirement Collection/weather Inquiry:
{
  "message": "I'm doing great! How about you? Where are you planning to go?"/"Hey, before creating your itinerary, could you tell me how many days you plan to stay?"/"The weather in {location} is {weather_info}.",
  "intent": "general_conversation"/"requirement_collection"/"weather_inquiry",
  "sessionId": "provided session ID or generate one",
  "timestamp": "current ISO timestamp",
  "itinerary": {}
}

2. Trip Planning (once all requirements are collected):
{
  "itinerary": {
    "Cities": [
      {
        "travel": {
          "from": "departure location",
          "to": "arrival city",
          "estimate_time": 0,
          "estimate_price": 0,
          "option": "flight/train/bus/car"
        },
        "Accomodation": {
          "name": "hotel name (from get_hotels_tool)",
          "description": "hotel description",
          "address": "hotel address",
          "geocode":{
            "latitude": 0.0,
            "longitude": 0.0
          },
          "rating": 0,
          "review_count": 0,
          "phone": "hotel phone number",
          "amenities": ["amenities list"],
          "price": {
            "amount": 0,
            "currency": "USD"
          },
          "guests": 0,
          "image_urls": ["MINIMUM 3 URLs from get_image_urls_tool"],
          "booking_url": "REAL booking URL or 'Contact directly'"
        },
        "days": [
          {
            "title": "Day 1",
            "date": "YYYY-MM-DD",
            "description": "Day summary",
            "day_number": "Day 1",
            "activities": [
              {
                "tag": "category",
                "title": "activity name (from get_activity_tool)",
                "description": "activity description",
                "minimum_duration": "time", # if not available give a approximate duration like "2-3 hours" 
                "booking_url": "REAL booking URL or 'Contact directly'",
                "address": "activity address",
                "NumberOfReview": 0,
                "Ratings": 0.0,
                "geocode":{
                  "latitude": 0.0,
                  "longitude": 0.0
                },
                "image_urls": ["MINIMUM 3 URLs from get_image_urls_tool"]
              }
            ]
          }
        ]
      }
    ],
    "overview": {
      "start_location": "departure city",
      "destination_location": "main destination",
      "summary": "brief trip summary",
      "duration_days": 0,
      "people_count": 0,
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "Estimated_overall_cost": 0,
      "image_urls": ["MINIMUM 3 URLs from get_image_urls_tool for overview"]
    }
  },
  "message": "Conversational trip summary for the user",
  "intent": "trip_planning",
  "sessionId": "provided session ID or generate one",
  "timestamp": "current ISO timestamp"
}
"""


    # Initialize the ReAct agent with trip planning tools
    self.agent = ReactAgent(
      tools=self.tools,
      model=model,
      system_prompt=self.system_prompt,
      provider=provider,
    )

  def process_trip_query(self, query: str, session_id: str = None) -> dict:
    """
    Process a trip planning query and return a comprehensive response.

    Args:
      query: The user's trip planning request
      session_id: Optional session ID for tracking

    Returns:
      dict: The structured trip planning response
    """
    try:
            # Generate session ID if not provided
            if not session_id:
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Add session context to the query with emphasis on tool usage
            enhanced_query = f"""Session ID: {session_id}
User Query: {query}

CRITICAL INSTRUCTIONS FOR THIS REQUEST:
You will be provided some previous conversation history and context analyze them and answer the user query accordingly.
1. You MUST use get_image_search_results_tool to get minimum 3 image URLs for  destination overview
2. NEVER use placeholder URLs or empty fields
3. Follow the exact JSON format specified in your system prompt
Please create a comprehensive trip plan following these mandatory requirements."""

            response = self.agent.run(enhanced_query, max_rounds=25)
            
            # Try to parse the response as JSON
            try:
                if isinstance(response, str):
                    # Look for JSON in the response
                    start_idx = response.find('{')
                    end_idx = response.rfind('}')
                    if start_idx != -1 and end_idx != -1:
                        json_str = response[start_idx:end_idx+1]
                        parsed_response = json.loads(json_str)
                        return parsed_response
                    
                # If no valid JSON found, create a basic structure
                return self._create_fallback_response(query, session_id, response)
                
            except json.JSONDecodeError:
                return self._create_fallback_response(query, session_id, response)
                
    except Exception as e:
      return self._create_error_response(query, session_id, str(e))
  
  def _create_fallback_response(self, query: str, session_id: str, agent_response: str) -> dict:
      """Load the saved fallback JSON if agent output is invalid."""
      try:
          with open("fall_back_res.txt", "r", encoding="utf-8") as f:
              saved_fallback = json.load(f)
              # Update sessionId and timestamp for consistency
              saved_fallback["sessionId"] = session_id
              saved_fallback["timestamp"] = datetime.now().isoformat()
              return saved_fallback
      except Exception as file_error:
          # If file fails to load, at least return minimal structure
          return {
              "message": f"Agent response invalid, and failed to load fallback file: {file_error}",
              "intent": "trip_planning",
              "sessionId": session_id,
              "timestamp": datetime.now().isoformat(),
              "itinerary": {}
          }

  
  def _create_error_response(self, query: str, session_id: str, error: str) -> dict:
      """Create an error response."""
      return {
          "message": f"I apologize, but I encountered an error while planning your trip: {error}. Please try rephrasing your request.",
          "Requirement_options": [query],
          "intent": "trip_planning",
          "sessionId": session_id,
          "timestamp": datetime.now().isoformat(),
          "itinerary": {
              "overview": {
                  "start_location": "",
                  "destination_location": "",
                  "summary": "Error occurred during planning",
                  "duration_days": 0,
                  "people_count": 0,
                  "start_date": "",
                  "end_date": "",
                  "image_urls": [],
                  "Estimated_overall_cost": 0
              },
              "Cities": []
          }
      }


# Helper function to create trip planning agent instance
def create_trip_agent(model: str = "gemini-2.0-flash-exp", provider=None) -> TripPlanningAgent:
  """
  Create and return a TripPlanningAgent instance.

  Args:
    model: The LLM model to use

  Returns:
    TripPlanningAgent: Configured trip planning agent
  """
  print(Fore.BLUE + "Model used:", Fore.YELLOW + model)
  if provider:
    print(Fore.BLUE + "Provider:", Fore.YELLOW + str(provider))
  return TripPlanningAgent(model=model, provider=provider)