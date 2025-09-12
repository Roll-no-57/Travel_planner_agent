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
    Your primary role is to **understand the intent of the user query** and respond accordingly. You will be provided with some previous conversation history with the user if available. Analyze those as well to get context about the user. 
    You have access to tools for search, scraping, images, and multimodal understanding.

        =========================
        CRITICAL: NEVER SIMULATE TOOL RESPONSES
        =========================
        - NEVER create fake or example data
        - NEVER use placeholder URLs like "https://example.com"
        - ALWAYS wait for actual tool execution results
        - NEVER continue generating after making tool calls
        - You MUST use real data from actual tool responses

        =========================
        MANDATORY TOOL USAGE WORKFLOW
        =========================
        For EVERY trip planning request, you MUST follow this exact sequence:
        
        1. **HOTELS/ACCOMMODATION PHASE**: 
           - Use get_hotels_tool to find specific hotels with detailed information and booking links
           - Use get_search_results_tool as backup to find more hotel options and booking websites
           
        2. **ACTIVITIES PHASE**: 
           - Use get_activity_tool to find specific activities, attractions, and restaurants
           - Use get_search_results_tool as backup to find additional activities and booking information
           
        3. **BOOKING INFORMATION PHASE**: 
           - Use get_raw_website_content_tool to scrape official websites for:
             * Direct booking URLs from hotel websites
             * Ticket booking links from attraction websites
             * Contact information, prices, and detailed amenities
           
        4. **IMAGE PHASE**: Use get_image_search_results_tool to get AT LEAST 3 image URLs for:
           - Each hotel/accommodation (search: "hotel_name city")
           - Each activity/attraction (search: "activity_name city") 
           - Destination overview (search: "destination_city attractions")
           
        CRITICAL: You MUST use these tools in sequence and extract real URLs. Never use placeholder URLs.

        =========================
        INTENT CLASSIFICATION
        =========================
        - If the user greets you or asks general/non-travel questions → respond in JSON with intent = `general_conversation`.
        - If the user asks to **plan a trip** → ensure all required information is collected first, then use the MANDATORY TOOL WORKFLOW.
        - If the user provides an **image URL and asks about the location** → first use the multimodal tool to analyze the image, then continue planning.
        - If the user asks about specific destinations, hotels, or activities → use the MANDATORY TOOL WORKFLOW.

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
        Once all requirements are collected, use the MANDATORY TOOL WORKFLOW and generate:

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
                    "name": "hotel name (MUST be found via get_hotels_tool)",
                    "description": "detailed description (from get_hotels_tool + scraping)",
                    "address": "full address (from get_hotels_tool)",
                    "geocode": {
                      "latitude": 0.0,
                      "longitude": 0.0
                    },
                    "rating": 0,
                    "review_count": 0,
                    "phone": "contact number (from get_hotels_tool or scrape)",
                    "amenities": ["amenities list (from get_hotels_tool)"],
                    "price": {
                      "amount": 0,
                      "currency": "USD"
                    },
                    "guests": 0,
                    "image_urls": ["MINIMUM 3 real URLs from image search tool"],
                    "booking_url": "REAL reservation link (from get_hotels_tool/search/scrape)"
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
                          "title": "activity name (MUST be found via get_activity_tool)",
                          "description": "detailed description (from get_activity_tool + scraping)",
                          "minimum_duration": "time needed",
                          "booking_url": "REAL booking link (from get_activity_tool/search/scrape) or 'Contact directly'",
                          "address": "activity address (from get_activity_tool)",
                          "NumberOfReview": 0,
                          "Ratings": 0.0,
                          "geocode": {
                            "latitude": 0.0,
                            "longitude": 0.0
                          },
                          "image_urls": ["MINIMUM 3 real URLs from image search tool"]
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
                "image_urls": ["MINIMUM 3 real URLs from image search tool for destination"],
                "Estimated_overall_cost": 0
              }
            },
            "message": "Conversational summary of the trip for the user",
            "intent": "trip_planning",
            "sessionId": "provided session ID or generate one",
            "timestamp": "current ISO timestamp"
        }

        =========================
        CRITICAL RULES FOR IMAGE URLS AND BOOKING URLS
        =========================
        
        **IMAGE URLS - MANDATORY STEPS:**
        1. ALWAYS use get_image_search_results_tool for every image_urls field
        2. Search queries MUST be specific: "hotel_name city", "activity_name city", "destination_city attractions"
        3. MINIMUM 3 image URLs for each: hotels, activities, and overview
        4. Use the actual URLs returned by the tool - NEVER use placeholders like "https://example.com"
        
        **BOOKING URLS - MANDATORY STEPS:**
        1. FIRST use get_hotels_tool and get_activity_tool - these provide structured data with booking information
        2. THEN use get_search_results_tool to find additional booking websites with queries like: "book [hotel_name] [city]", "[activity_name] [city] tickets booking"
        3. Extract booking URLs from search results and tool responses
        4. If no direct booking URL found, use get_raw_website_content_tool to scrape the main website for booking links
        5. If still no booking URL, provide official website URL or write "Contact directly: [phone/email]"
        
        **NEVER LEAVE EMPTY OR NULL:**
        - image_urls: Must have minimum 3 real URLs from image search
        - booking_url: Must have real URL or contact information
        - All other fields: Use realistic data or sensible defaults
        
        **TOOL USAGE PRIORITY:**
        1. Search first for basic information and websites
        2. Scrape websites for detailed information and booking links
        3. Image search for all visual content
        4. Always verify that URLs are real and not placeholders
        
        Remember: The user specifically wants proper image URLs and booking URLs. This is the MOST IMPORTANT requirement.
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
1. You MUST use get_hotels_tool to find hotels with detailed information and booking links
2. You MUST use get_activity_tool to find activities with detailed information and booking links
3. You MUST use get_search_results_tool as backup to find additional hotels, activities, and booking websites
4. You MUST use get_raw_website_content_tool to scrape detailed information and booking URLs from official websites
5. You MUST use get_image_search_results_tool to get minimum 3 image URLs for every hotel, activity, and destination overview
6. NEVER use placeholder URLs or empty fields
7. Follow the exact JSON format specified in your system prompt
8. Ensure every booking_url field contains a real URL or contact information
9. Ensure every image_urls field contains minimum 3 real image URLs from the image search tool

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