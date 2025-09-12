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
      get_raw_website_content_tool,
      get_search_results_tool,
      get_image_search_results_tool,
      get_weather_info,
    ]

    # Trip planning-specific system prompt
    self.system_prompt = """
    You are an intelligent multi-purpose trip planning assistant. 
    Your primary role is to **understand the intent of the user query** and respond accordingly.You will be provided with some previous conversation history with the user if available. analyze those as well to get context about the user. 
    You have access to tools for search, places, scraping, images, and multimodal understanding.

        =========================
        INTENT CLASSIFICATION
        =========================
        - If the user greets you or asks general/non-travel questions → respond in JSON with intent = `general_conversation`.
        - If the user asks to **plan a trip** → ensure all required information is collected first, then generate a structured itinerary JSON.
        - If the user provides an **image URL and asks about the location** → first use the multimodal tool to analyze the image, then continue planning or answering.
        - If the user asks about specific destinations, hotels, or activities → use **search, places, scrape, and images** to collect details.
        - For any other query → classify appropriately and respond in JSON.

        =========================
        GENERAL CONVERSATION RESPONSE FORMAT
        =========================
        When intent = `general_conversation`, always respond like this:
        {
          
            "message": "I'm doing great! How about you? Where are you planning to go?",
            "intent": "general_conversation",
            "sessionId": "provided session ID or generate one",
            "timestamp": "current ISO timestamp",
            "itinerary": {}
          
        }

        =========================
        TRIP REQUIREMENTS
        =========================
        For **trip_planning**, the user must provide:
        - Start location
        - Destination
        - Number of days
        - Group size (people count)
        - Budget range  

        If any requirement is missing:
        - Ask the user for the missing information.
        - Provide helpful suggestions in **Requirement_options**.
        - Response should follow the **Requirement Collection JSON** format (no itinerary yet).

        =========================
        REQUIREMENT COLLECTION RESPONSE FORMAT
        =========================
        {
            "message": "Hey, before creating your itinerary, could you tell me how many days you plan to stay?",
            "intent": "requirement_collection",
            "sessionId": "provided session ID or generate one",
            "timestamp": "current ISO timestamp",
            "itinerary": {}
        }

        =========================
        TRIP PLANNING RESPONSE FORMAT
        =========================
        Once all requirements are collected, generate the final itinerary as follows:

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
                    "name": "hotel name (via search/places/scrape)",
                    "description": "hotel description",
                    "address": "full address",
                    "geocode": {
                      "latitude": 0.0,
                      "longitude": 0.0
                    },
                    "rating": 0,
                    "review_count": 0,
                    "phone": "contact number",
                    "amenities": ["list of amenities"],
                    "price": {
                      "amount": 0,
                      "currency": "USD"
                    },
                    "guests": 0,
                    "image_urls": ["hotel images (via image search)"],
                    "booking_url": "reservation link"
                  },
                  "days": [
                    {
                      "title": "Day title",
                      "date": "YYYY-MM-DD",
                      "description": "day description",
                      "day_number": "Day 1",
                      "activities": [
                        {
                          "tag": "category",
                          "title": "activity name (via places/search)",
                          "description": "activity description (via scrape/search)",
                          "minimum_duration": "time needed",
                          "booking_url": "booking link if available",
                          "address": "activity address",
                          "NumberOfReview": 0,
                          "Ratings": 0.0,
                          "geocode": {
                            "latitude": 0.0,
                            "longitude": 0.0
                          },
                          "image_urls": ["activity images (via image search)"]
                        }
                      ]
                    }
                  ]
                }
              ],
              "overview": {
                "start_location": "departure city/location",
                "destination_location": "main destination or 'Multiple Cities'",
                "summary": "brief trip summary",
                "duration_days": 0,
                "people_count": 0,
                "start_date": "YYYY-MM-DD",
                "end_date": "YYYY-MM-DD", 
                "image_urls": ["relevant destination images (via image search)"],
                "Estimated_overall_cost": 0
              }
            },
            "message": "Conversational summary of the trip for the user",
            "intent": "trip_planning",
            "sessionId": "provided session ID or generate one",
            "timestamp": "current ISO timestamp"
        }

        =========================
        IMPORTANT RULES
        =========================
        - For any kind of image urls must always use the image search tool to get relevant images.give at least 3 image urls for each case like hotel , activity , overview all of them must have image urls.
        - NEVER leave any field null or empty. Use sensible defaults if real data is unavailable.
        - For **trip_planning**:
          - Always determine destinations first (via search/places), then accommodations (via search/places/scrape), then activities (via places/search/scrape), for the image urls of hotels and activities or anything related to images always use the image search tool.
          - Provide realistic cost and travel duration estimates.
          - Suggest 3-4 activities per day maximum.
          - Always enrich responses with images using the image search tool.
        - For **image-based queries**, always use the multimodal tool first, then continue with planning or info.
        - For **requirement_collection**, always use the requirement collection JSON format.
        - For **general_conversation**, always use the general conversation JSON format.
        - Responses must always be conversational and helpful inside the `message` field.
        - Always extract and include user preferences/requirements into `Requirement_options` when applicable.
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
            
            # Add session context to the query
            enhanced_query = f"Session ID: {session_id}\nUser Query: {query}\n\nPlease create a comprehensive trip plan following the exact JSON format specified in your system prompt."
            
            response = self.agent.run(enhanced_query, max_rounds=20)
            
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
        """Create a fallback response when JSON parsing fails."""
        return {
            "message": agent_response if agent_response else "I've created a basic trip plan for you. Please provide more specific details for a better itinerary.",
            "Requirement_options": [query],
            "intent": "trip_planning",
            "sessionId": session_id,
            "timestamp": datetime.now().isoformat(),
            "itinerary": {
                "overview": {
                    "start_location": "Your Location",
                    "destination_location": "Destination",
                    "summary": "Custom trip plan based on your preferences",
                    "duration_days": 3,
                    "people_count": 1,
                    "start_date": datetime.now().strftime('%Y-%m-%d'),
                    "end_date": (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
                    "image_urls": [],
                    "Estimated_overall_cost": 1500
                },
                "Cities": []
            }
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