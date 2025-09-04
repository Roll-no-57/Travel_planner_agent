from Planning_agent import ReactAgent
from colorama import Fore, Style, init
import json
from datetime import datetime, timedelta

from Tools.get_activity_tool import get_activity_tool
from Tools.get_hotels_tool import get_hotels_tool
# from Tools.vision_capability_tool import get_multimodal_capability  # Temporarily disabled
from Tools.web_scrape_tool import get_raw_website_content_tool
from Tools.web_search_tool import get_search_results_tool


class TripPlanningAgent:
    """
    A comprehensive trip planning agent that can answer various travel-related queries
    using natural language processing and multiple travel data sources.
    """
    
    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize the Trip Planning Agent with all necessary tools.
        
        Args:
            model: The LLM model to use for reasoning
        """
        # Define all trip planning-related tools
        self.tools = [
            get_activity_tool,
            get_hotels_tool,
            # get_multimodal_capability,  # Temporarily disabled
            get_raw_website_content_tool,
            get_search_results_tool
        ]

        # Trip planning-specific system prompt
        self.system_prompt = """
You are an expert trip planning assistant that creates comprehensive travel itineraries. Your task is to help users plan amazing trips by following these steps:

1. SEARCH FOR DESTINATIONS: Use web search to find the best cities/destinations/towns based on user requirements
2. FIND ACCOMMODATIONS: For each destination, find the best hotel/accommodation using the hotels tool
3. DISCOVER ACTIVITIES: Find top activities and attractions in each city using the activities tool
4. CREATE STRUCTURED RESPONSE: Always respond with a complete JSON structure matching the exact format specified

CRITICAL RESPONSE FORMAT:
You must ALWAYS return a JSON response in this exact structure:

{
  "message": "Your conversational response to the user",
  "Requirement_options": ["extracted user preferences/requirements"],
  "intent": "trip_planning",
  "sessionId": "provided session ID or generate one",
  "timestamp": "current ISO timestamp",
  "itinerary": {
    "overview": {
      "start_location": "departure city/location",
      "destination_location": "main destination or 'Multiple Cities'",
      "summary": "brief trip summary",
      "duration_days": 0,
      "people_count": 0,
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD", 
      "image_urls": ["relevant destination images"],
      "Estimated_overall_cost": 0
    },
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
          "name": "hotel name",
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
          "image_urls": ["hotel images"],
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
                "title": "activity name",
                "description": "activity description",
                "minimum_duration": "time needed",
                "booking_url": "booking link",
                "address": "activity address",
                "NumberOfReview": 0,
                "Ratings": 0.0,
                "geocode": {
                  "latitude": 0.0,
                  "longitude": 0.0
                },
                "image_urls": ["activity images"]
              }
            ]
          }
        ]
      }
    ]
  }
}

IMPORTANT RULES:
- NEVER leave any field null or empty - if data is missing from tools, use reasonable estimates or defaults
- Always provide realistic cost estimates and durations
- Include at least 2-3 activities per day
- Ensure all geocode coordinates are valid numbers
- Make responses conversational and helpful
- Extract user requirements from their query for Requirement_options
- Always search for destinations first, then hotels, then activities for each city
"""
        
        # Initialize the ReAct agent with trip planning tools
        self.agent = ReactAgent(
            tools=self.tools,
            model=model,
            system_prompt=self.system_prompt
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
def create_trip_agent(model: str = "gemini-2.0-flash-exp") -> TripPlanningAgent:
    """
    Create and return a TripPlanningAgent instance.
    
    Args:
        model: The LLM model to use
        
    Returns:
        TripPlanningAgent: Configured trip planning agent
    """
    print(Fore.BLUE + "Model used:", Fore.YELLOW + model)
    return TripPlanningAgent(model=model)