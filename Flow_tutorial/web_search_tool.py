import json
import requests
# from tool_decorator import tool
from dotenv import load_dotenv
import os
from crewai.tools import tool


load_dotenv()

@tool
def get_search_results_tool(query: str, max_results: int = 4) -> str:
    """
    Search the internet for information on a given topic.
    Returns relevant search results with titles, links, and snippets.
    
    Args:
        query: The search query to look up (e.g., "best restaurants in Paris")
        max_results: Maximum number of search results to return (default: 4)
    """
    try:
        # Get the Serper API key from environment variables
        serper_api_key = os.getenv("SERPER_API_KEY")
        if not serper_api_key:
            return "Error: SERPER_API_KEY not found in environment variables"
        
        # Perform search request
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': serper_api_key,
            'content-type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        
        if response.status_code != 200:
            return f"Error: Search API request failed. Status code: {response.status_code}"
        
        data = response.json()
        if 'organic' not in data:
            return "No results found or API error occurred."
        
        # Process search results
        results = data['organic']
        search_results = []
        
        for i, result in enumerate(results[:max_results]):
            try:
                search_result = {
                    "position": i + 1,
                    "title": result.get('title', 'No title available'),
                    "link": result.get('link', 'No link available'),
                    "snippet": result.get('snippet', 'No snippet available'),
                    "source": result.get('displayLink', 'Unknown source')
                }
                search_results.append(search_result)
            except Exception as e:
                continue
        
        # Structure the final result
        final_result = {
            "search_query": query,
            "total_results": len(search_results),
            "results": search_results
        }
        
        return json.dumps(final_result, indent=2)
        
    except Exception as e:
        return f"Error during search: {str(e)}"

