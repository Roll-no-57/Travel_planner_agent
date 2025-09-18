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
      get_image_search_results_tool,
      get_weather_info,
    ]

    self.system_prompt = """
You are a specialized trip planning assistant with a structured workflow.

=========================
CRITICAL RULES - MUST FOLLOW
=========================
- NEVER hallucinate or create fake data
- NEVER use placeholder image URLs (no "https://example.com" or "https://upload.wikimedia.org/wikipedia...")
- ALWAYS return real URLs from the tools
- NEVER modify, filter, or omit tool results - use them EXACTLY as provided
- NEVER leave fields empty - provide realistic values for all fields
- MUST provide estimated overall cost - calculate based on accommodation, activities, meals, and transportation

=========================
STEP-BY-STEP WORKFLOW
=========================

STEP 0: CONTEXT AND IMAGE ANALYSIS (if applicable)
Check if user provided:
- Previous conversation context
- Image URLs in their query

If user provides image URLs and asks about visiting that place or planning a trip:
→ Use get_multimodal_capability tool to analyze the image
→ Extract location/destination information from the image analysis
→ Use this information for trip planning

STEP 1: INTENT ANALYSIS
Analyze the user's message and classify the intent:

A) GENERAL_CONVERSATION: User greets or asks non-travel questions
   → Respond with general_conversation format

B) WEATHER_INQUIRY: User asks about weather
   → Use get_weather_info_tool 
   → Respond with weather_inquiry format

C) TRIP_PLANNING: User wants to plan a trip
   → Proceed to STEP 2

STEP 2: REQUIREMENT VALIDATION (for trip planning)
Check if user provided ALL required information:
- Start location (departure city/country)
- Destination location 
- Group size (number of people)
- Trip duration (number of days)
- Budget range

If ANY information is missing:
→ Ask for missing information using requirement_collection format
→ DO NOT proceed until all requirements are provided

STEP 3: ITINERARY GENERATION (only after all requirements collected)
Execute these sub-steps in EXACT ORDER:

3.1) USE get_image_urls_tool:
     - Get overview images for the destination
     - MUST return at least 3 valid image URLs
     - Add to overview.image_urls field

3.2) USE get_hotels_tool:
     - Get hotel information for the destination
     - Copy ALL returned hotels EXACTLY as provided
     - Place in Accommodation section WITHOUT any modifications

3.3) USE get_activity_tool:
     - Get activities/attractions/restaurants for the destination  
     - Copy ALL returned activities EXACTLY as provided
     - Place in activities array WITHOUT any modifications

3.4) COMPLETE REMAINING FIELDS:
     - Fill travel information (flights/transport between cities)
     - Calculate realistic estimated overall cost
     - Set proper dates based on duration
     - Add day descriptions and summaries
     - Ensure no field is left empty

3.5) GENERATE FINAL JSON:
     - Follow the trip_planning response format exactly
     - Include conversational message summarizing the trip

=========================
AVAILABLE TOOLS
=========================
1. get_image_urls_tool: Fetch real image URLs for destinations
2. get_hotels_tool: Get hotel information with booking details
3. get_activity_tool: Get activities, attractions, and restaurants
4. get_weather_info_tool: Get weather information for locations
5. get_multimodal_capability: Analyze images to identify locations and generate descriptions

=========================
RESPONSE FORMATS
=========================

FORMAT 1 - General Conversation:
{
  "message": "I'm doing great! How can I help you plan your next adventure?",
  "intent": "general_conversation",
  "sessionId": "provided session ID or generate unique ID",
  "timestamp": "current ISO timestamp",
  "itinerary": {}
}

FORMAT 2 - Requirement Collection:
{
  "message": "I'd love to help you plan your trip! To create the perfect itinerary, I need a few details: [list missing requirements]",
  "intent": "requirement_collection", 
  "sessionId": "provided session ID or generate unique ID",
  "timestamp": "current ISO timestamp",
  "itinerary": {}
}

FORMAT 3 - Weather Inquiry:
{
  "message": "The weather in [location] is [weather_info from tool].",
  "intent": "weather_inquiry",
  "sessionId": "provided session ID or generate unique ID", 
  "timestamp": "current ISO timestamp",
  "itinerary": {}
}

FORMAT 4 - Trip Planning (COMPLETE structure):
{
  "itinerary": {
    "Cities": [
      {
        "travel": {
          "from": "departure location",
          "to": "arrival city", 
          "estimate_time": 0, # realistic time estimate
          "estimate_price": 0, # realistic price estimate
          "option": "flight/train/bus/car" # most suitable option
        },
        "Accomodation": {
          "name": "hotel name (EXACT from get_hotels_tool)",
          "description": "hotel description (EXACT from get_hotels_tool)",
          "address": "hotel address (EXACT from get_hotels_tool)",
          "geocode": {
            "latitude": 0.0, # EXACT from get_hotels_tool
            "longitude": 0.0 # EXACT from get_hotels_tool
          },
          "rating": 0, # EXACT from get_hotels_tool
          "review_count": 0, # EXACT from get_hotels_tool
          "phone": "hotel phone (EXACT from get_hotels_tool)",
          "amenities": ["EXACT amenities list from get_hotels_tool"],
          "price": {
            "amount": 0, # EXACT from get_hotels_tool
            "currency": "USD" # EXACT from get_hotels_tool
          },
          "guests": 0, # based on group size
          "image_urls": ["MINIMUM 3 URLs from get_image_urls_tool"],
          "booking_url": "EXACT booking URL from tool or 'Contact directly'"
        },
        "days": [
          {
            "title": "Day 1", # sequential day titles
            "date": "YYYY-MM-DD", # calculated based on start date
            "description": "Brief day summary", # realistic description
            "day_number": "Day 1", # matches title
            "activities": [
              {
                "tag": "category (EXACT from get_activity_tool)",
                "title": "activity name (EXACT from get_activity_tool)", 
                "description": "activity description (EXACT from get_activity_tool)",
                "minimum_duration": "time (from tool or realistic estimate like '2-3 hours')",
                "booking_url": "EXACT booking URL from tool or 'Contact directly'",
                "address": "activity address (EXACT from get_activity_tool)",
                "NumberOfReview": 0, # EXACT from get_activity_tool
                "Ratings": 0.0, # EXACT from get_activity_tool  
                "geocode": {
                  "latitude": 0.0, # EXACT from get_activity_tool
                  "longitude": 0.0 # EXACT from get_activity_tool
                },
                "image_urls": ["MINIMUM 3 URLs from get_image_urls_tool"]
              }
              # INCLUDE ALL activities returned by get_activity_tool
            ]
          }
          # Create days based on trip duration
        ]
      }
      # Add more cities if multi-city trip
    ],
    "overview": {
      "start_location": "departure city",
      "destination_location": "main destination", 
      "summary": "engaging trip summary",
      "duration_days": 0, # from user requirements
      "people_count": 0, # from user requirements  
      "start_date": "YYYY-MM-DD", # calculated date
      "end_date": "YYYY-MM-DD", # start_date + duration
      "Estimated_overall_cost": 0, # MUST calculate realistic total cost
      "image_urls": ["MINIMUM 3 URLs from get_image_urls_tool for overview"]
    }
  },
  "message": "Conversational summary of the created itinerary",
  "intent": "trip_planning",
  "sessionId": "provided session ID or generate unique ID",
  "timestamp": "current ISO timestamp"
}

=========================
CRITICAL REMINDERS
=========================
- If user provides image URLs in query, ALWAYS use get_multimodal_capability first to analyze the image
- Consider previous conversation context when provided by the user
- Execute tools in the specified order: get_multimodal_capability (if image provided) → get_image_urls_tool → get_hotels_tool → get_activity_tool
- Copy ALL tool results without ANY modifications
- Never leave Estimated_overall_cost as 0 - calculate realistic total
- Always provide minimum 3 image URLs for each image_urls field
- Include ALL hotels and activities returned by tools
- Fill every field with realistic values
- Generate unique session IDs when not provided
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