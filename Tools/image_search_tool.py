import json
import requests
from tool_decorator import tool
from dotenv import load_dotenv
import os

load_dotenv()

@tool
def get_image_search_results_tool(query: str, max_results: int = 5) -> str:
    """
    Search for images on the internet using Serper's image search API.
    Returns relevant image results with titles, links, and image URLs.
    
    Args:
        query: The search query to look up (e.g., "apple inc", "sunset beach")
        max_results: Maximum number of image results to return (default: 4)
    """
    try:
        # Get the Serper API key from environment variables
        serper_api_key = os.getenv("SERPER_API_KEY")
        if not serper_api_key:
            return "Error: SERPER_API_KEY not found in environment variables"
        
        # Perform image search request
        url = "https://google.serper.dev/images"
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': serper_api_key,
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        
        if response.status_code != 200:
            return f"Error: Image search API request failed. Status code: {response.status_code}"
        
        data = response.json()
        if 'images' not in data:
            return "No image results found or API error occurred."
        
        # Process image search results
        results = data['images']
        image_results = []
        
        # Fixed: Use enumerate correctly to get both index and result
        for i, result in enumerate(results[:max_results]):
            try:
                image_result = result.get('imageUrl', 'No image URL available')
                image_results.append(image_result)
            except Exception as e:
                continue
        # Structure the final result
        final_result = {
            "search_query": query,
            "total_results": len(image_results),
            "results": image_results
        }
        
        return json.dumps(final_result, indent=2)
        
    except Exception as e:
        return f"Error during image search: {str(e)}"









#========================== Test the image search tool ==========================
def test_image_search():
    """Test the image search tool with various queries"""
    
    # Test cases
    test_queries = [
        "apple inc logo",
        "sunset beach",
        "cute cats",
        "python programming"
    ]
    
    print("Testing Serper Image Search Tool")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        print("-" * 30)
        
        try:
            result = get_image_search_results_tool(query, max_results=3)
            print(result)
            
            # Parse the JSON result for pretty printing
            parsed_result = json.loads(result)
            print(f"Found {parsed_result['total_results']} results")
            
            for img in parsed_result['results']:
                print(f"  {img['position']}. {img['title']}")
                print(f"     Image: {img['image_url']}")
                print(f"     Source: {img['source']}")
                print(f"     Size: {img['width']}x{img['height']}")
                print()
                
        except json.JSONDecodeError:
            print(f"Error or non-JSON response: {result}")
        except Exception as e:
            print(f"Error testing query '{query}': {str(e)}")

if __name__ == "__main__":
    test_image_search()