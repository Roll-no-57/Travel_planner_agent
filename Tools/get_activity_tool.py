from apify_client import ApifyClient
import json

from dotenv import load_dotenv
from tool_decorator import tool

import os

load_dotenv()



@tool
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
            "includeTags": False,
            "includeNearbyResults": False,
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
            # Safely handle latitude and longitude conversion
            latitude = item.get("latitude")
            longitude = item.get("longitude")
            
            # Convert to float if not None, otherwise use 0.0
            try:
                lat_float = float(latitude) if latitude is not None else 0.0
            except (ValueError, TypeError):
                lat_float = 0.0
                
            try:
                lon_float = float(longitude) if longitude is not None else 0.0
            except (ValueError, TypeError):
                lon_float = 0.0
            
            # Safely handle rating conversion
            rating = item.get("rating")
            try:
                rating_float = float(rating) if rating is not None else 0.0
            except (ValueError, TypeError):
                rating_float = 0.0
            
            activity = {
                "tag": item.get("category", "attraction"),
                "title": item.get("name") or item.get("locationString") or "Unknown",
                "description": item.get("description", f"{item.get('name', 'Place')} in {item.get('locationString','Unknown')}"),
                "minimum_duration": "1-2 hours",  # Default
                "booking_url": item.get("webUrl") or item.get("website"),
                "address": item.get("address", "Address not available"),
                "geocode": {
                    "latitude": lat_float,
                    "longitude": lon_float
                },
                "NumberOfReviews": item.get("numberOfReviews", 0),
                "Rating": rating_float,
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
    