from apify_client import ApifyClient
import json

from tool_decorator import tool
from dotenv import load_dotenv

import os


load_dotenv()


@tool
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
            "currency": "USD",
            "includeAiReviewsSummary": False,
            "includeAttractions": False,
            "includeHotels": True,      
            "includeNearbyResults": False,
            "includePriceOffers": False, 
            "includeRestaurants": False,
            "includeTags": False,
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
            
            hotel = {
                "name": item.get("name") or item.get("locationString") or "Unknown Hotel",
                "description": item.get("description", f"{item.get('name', 'Hotel')} in {item.get('locationString','Unknown')}"),
                "booking_url": item.get("webUrl") or item.get("website"),
                "address": item.get("address", "Address not available"),
                "geocode": {
                    "latitude": lat_float,
                    "longitude": lon_float
                },
                "phone": item.get("phone"),
                "number_of_reviews": item.get("numberOfReviews", 0),
                "rating": rating_float,
                "price_range": item.get("priceRange"),
                "amenities": item.get("amenities"),
                "image_urls": item.get("photos", [])[:5] if item.get("photos") else []
            }
            hotels.append(hotel)

        result = {"hotels": hotels}
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return f"Error searching hotels: {str(e)}"

