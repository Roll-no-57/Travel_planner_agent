from apify_client import ApifyClient
import json

from crewai.tools import tool
from crewai import Agent, Task, Crew
from dotenv import load_dotenv

import os

load_dotenv()



@tool("get_activities")
def get_activity_tool(location: str, max_items: int = 2) -> str:
    """
    Search for activities, attractions, and restaurants in a specific location.
    Returns formatted activity data including attractions, restaurants, and places to visit.
    
    Args:
        location: The city or location to search for (e.g., "Chicago,USA", "Lauterbrunnen,Switzerland", "London,UK")
        max_items: Maximum number of items to return (default: 10)
    """
    try:
        # Initialize the ApifyClient with your API token
        client = ApifyClient(os.getenv("APIFY_API_TOKEN"))
        
        # Prepare the Actor input
        run_input = {
            "query": location,
            "maxItemsPerQuery": max_items,
            "includeTags": True,
            "includeNearbyResults": True,
            "includeAttractions": True,
            "includeRestaurants": True,
            "includeHotels": False,
            "includeVacationRentals": False,
            "includePriceOffers": False,
            "includeAiReviewsSummary": False,
            "language": "en",
            "currency": "USD",
        }
        
        # Run the Actor and wait for it to finish
        run = client.actor("dbEyMBriog95Fv8CW").call(
            run_input=run_input,
            logger=None
        )
        
        # Fetch Actor results from the run's dataset
        activities = []

        # Fetch and filter results
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            activity = {
                "tag": item.get("category"),
                "title": item.get("name") or item.get("locationString") or "Unknown",
                "description": item.get("description", f"{item.get('name', 'Place')} in {item.get('locationString','Unknown')}"),
                "minimum_duration": "1-2 hours",  # Default
                "booking_url": item.get("webUrl") or item.get("website"),
                "address": item.get("address", "Address not available"),
                "geocode": {
                    "latitude": float(item.get("latitude", 0.0)),
                    "longitude": float(item.get("longitude", 0.0))
                },
                "NumberOfReviews": item.get("numberOfReviews", 0),
                "Rating": item.get("rating", 0.0),
                "image_urls": item.get("photos", [])[:5] if item.get("photos") else []
            }
            activities.append(activity)
            # print(activity)

        result = {
                    "activities": activities
                }
        print(activities)
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return f"Error searching activities: {str(e)}"
    
    
    
    
    
    


#============================For testing purpose==================================

# Create Activity Search Agent
activity_agent = Agent(
    role='Activity Coordinator',
    goal='Find and organize exciting activities, attractions, and dining options for travelers',
    backstory='''You are an enthusiastic activity coordinator who specializes in 
    discovering amazing experiences for travelers. You know how to find the best 
    attractions, restaurants, and activities in any location, and you always 
    provide comprehensive details to help people plan their trips.search at most 3 activities''',
    tools=[get_activity_tool],
    verbose=True,
    llm="gemini/gemini-1.5-flash"
)

# Create Activity Search Task
activity_task = Task(
    description='''Search for activities, attractions, and restaurants in Lauterbrunnen, Switzerland. 
    Find the top recommendations including tourist attractions, good restaurants, and interesting 
    places to visit. Provide comprehensive information about each activity.Use the tool once if it gives complete results.''',
    expected_output='''A detailed JSON-formatted list of activities in Lauterbrunnen, Switzerland 
    including attractions, restaurants, and other points of interest. Each activity should include 
    title, description, address, coordinates, and image URLs.''',
    agent=activity_agent
)

def test_activity_crew():
    """Test the activity search crew"""
    print("Activity Search Crew Test")
    print("=" * 30)
    
    # Create the crew
    activity_crew = Crew(
        agents=[activity_agent],
        tasks=[activity_task],
        verbose=True,
        llm="gemini/gemini-1.5-flash"
    )
    
    # Execute the task
    result = activity_crew.kickoff()
    
    print("\nFinal Activity Search Result:")
    print("=" * 40)
    print(result)
    return result

def main():
    """Main function to test the activity tool"""
    test_activity_crew()

if __name__ == "__main__":
    main()