import json
import requests
from tool_decorator import tool
from dotenv import load_dotenv
import os

load_dotenv()

@tool
def get_place_search_results_tool(query: str, max_results: int = 5) -> str:
    """
    Search for places on the internet using Serper's place search API.
    Returns relevant place results with names, addresses, ratings, and other details.
    
    Args:
        query: The search query to look up (e.g., "apple inc", "restaurants near me", "hotels in paris")
        max_results: Maximum number of place results to return (default: 5)
    """
    try:
        # Get the Serper API key from environment variables
        serper_api_key = os.getenv("SERPER_API_KEY")
        if not serper_api_key:
            return "Error: SERPER_API_KEY not found in environment variables"
        
        # Perform place search request
        url = "https://google.serper.dev/places"
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': serper_api_key,
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        
        if response.status_code != 200:
            return f"Error: Place search API request failed. Status code: {response.status_code}"
        
        data = response.json()
        if 'places' not in data:
            return "No place results found or API error occurred."

        # Process place search results
        results = data['places']
        place_results = []
        
        # Process each place result
        for i, result in enumerate(results[:max_results]):
            try:
                place_result = {
                    "position": i + 1,
                    "title": result.get('title', 'No title available'),
                    "address": result.get('address', 'No address available'),
                    "phone": result.get('phoneNumber', 'No phone available'),
                    "website": result.get('website', 'No website available'),
                    "rating": result.get('rating', 'No rating available'),
                    "reviews": result.get('reviews', 'No reviews available'),
                    "type": result.get('type', 'No type available'),
                    "price_level": result.get('priceLevel', 'No price level available'),
                    "latitude": result.get('latitude', 'No latitude available'),
                    "longitude": result.get('longitude', 'No longitude available'),
                    "plus_code": result.get('plusCode', 'No plus code available')
                }
                place_results.append(place_result)
            except Exception as e:
                continue
        
        # Structure the final result
        final_result = {
            "search_query": query,
            "total_results": len(place_results),
            "results": place_results
        }
        
        return json.dumps(final_result, indent=2)
        
    except Exception as e:
        return f"Error during place search: {str(e)}"

#========================== Test the place search tool ==========================
def test_place_search():
    """Test the place search tool with various queries"""
    
    # Test cases
    test_queries = [
        "apple inc",
        "restaurants in new york",
        "hotels in paris",
        "coffee shops near times square"
    ]
    
    print("Testing Serper Place Search Tool")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        print("-" * 30)
        
        try:
            result = get_place_search_results_tool(query, max_results=3)
            print(result)
            
            # Parse the JSON result for pretty printing
            parsed_result = json.loads(result)
            print(f"Found {parsed_result['total_results']} results")
            
            for place in parsed_result['results']:
                print(f"  {place['position']}. {place['title']}")
                print(f"     Address: {place['address']}")
                print(f"     Phone: {place['phone']}")
                print(f"     Rating: {place['rating']}")
                print(f"     Website: {place['website']}")
                print()
                
        except json.JSONDecodeError:
            print(f"Error or non-JSON response: {result}")
        except Exception as e:
            print(f"Error testing query '{query}': {str(e)}")

if __name__ == "__main__":
    test_place_search()
