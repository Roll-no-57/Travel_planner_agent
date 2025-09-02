from apify_client import ApifyClient
import json

from crewai.tools import tool
from crewai import Agent, Task, Crew
from dotenv import load_dotenv

import os


load_dotenv()


@tool("get_hotels")
def get_hotels_tool(location: str, checkinDate: str, checkoutDate: str, max_items: int = 1) -> str:
    """
    Search for hotels in a specific location.
    Returns formatted hotel data including name, description, address, geocode,
    number of reviews, rating, price range, amenities, contact info, and images.
    
    Args:
        location: The city or location to search for hotels (e.g., "Chicago,USA", "Lauterbrunnen,Switzerland")
        checkinDate: Check-in date in YYYY-MM-DD format
        checkoutDate: Check-out date in YYYY-MM-DD format
        max_items: Maximum number of hotels to return (default: 1)
    """
    try:
        # Initialize the ApifyClient with your API token
        client = ApifyClient(os.getenv("APIFY_API_TOKEN"))
        
        # Prepare the Actor input
        run_input = {
            "checkInDate": "2025-09-03",
            "checkOutDate": "2025-09-04",
            "currency": "USD",
            "includeAiReviewsSummary": False,
            "includeAttractions": False,
            "includeHotels": True,      
            "includeNearbyResults": True,
            "includePriceOffers": True, 
            "includeRestaurants": False,
            "includeTags": True,
            "includeVacationRentals": False,
            "language": "en",
            "maxItemsPerQuery": max_items,
            "query": location
        }
        
        # Run the Actor and wait for it to finish (disable logging noise)
        run = client.actor("dbEyMBriog95Fv8CW").call(
            run_input=run_input,
            logger=None,
        )
        
        # Fetch Actor results from the run's dataset
        hotels = []

        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            hotel = {
                "name": item.get("name") or item.get("locationString") or "Unknown Hotel",
                "description": item.get("description", f"{item.get('name', 'Hotel')} in {item.get('locationString','Unknown')}"),
                "booking_url": item.get("webUrl") or item.get("website"),
                "address": item.get("address", "Address not available"),
                "geocode": {
                    "latitude": float(item.get("latitude", 0.0)),
                    "longitude": float(item.get("longitude", 0.0))
                },
                "phone": item.get("phone"),
                "number_of_reviews": item.get("numberOfReviews", 0),
                "rating": item.get("rating", 0.0),
                "price_range": item.get("priceRange"),
                "amenities": item.get("amenities"),
                "image_urls": item.get("photos", [])[:5] if item.get("photos") else []
            }
            hotels.append(hotel)

        result = {"hotels": hotels}
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return f"Error searching hotels: {str(e)}"


# ======================================== For testing purpose ======================================================

# Create Hotel Search Agent
hotel_agent = Agent(
    role='Hotel Finder',
    goal='Find and organize the best hotels for travelers in a given destination',
    backstory='''You are a hotel specialist who knows how to find the best accommodations 
    for travelers. You provide detailed information about hotels including price ranges, 
    amenities, ratings, and location.''',
    tools=[get_hotels_tool],
    verbose=True,
    llm="gemini/gemini-1.5-flash"
)

# Create Hotel Search Task
hotel_task = Task(
    description='''Search for hotels in Lauterbrunnen, Switzerland. 
    Find top recommendations and provide detailed hotel information.''',
    expected_output='''A JSON-formatted list of hotels in Lauterbrunnen, Switzerland 
    including name, description, address, coordinates, rating, number of reviews, 
    price range, amenities, and image URLs.''',
    agent=hotel_agent
)

def test_hotel_crew():
    """Test the hotel search crew"""
    print("Hotel Search Crew Test")
    print("=" * 30)
    
    # Create the crew
    hotel_crew = Crew(
        agents=[hotel_agent],
        tasks=[hotel_task],
        verbose=True,
        llm="gemini/gemini-1.5-flash"
    )
    
    # Execute the task
    result = hotel_crew.kickoff()
    
    print("\nFinal Hotel Search Result:")
    print("=" * 40)
    print(result)
    return result

def main():
    """Main function to test the hotel tool"""
    test_hotel_crew()

if __name__ == "__main__":
    main()
