import json
import requests
from crewai.tools import tool
from crewai import Agent, Task, Crew
from dotenv import load_dotenv
import os

load_dotenv()

@tool("get_search_results")
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


# ======================================== For testing purpose ======================================================

# Create Search Agent
search_agent = Agent(
    role='Internet Research Specialist',
    goal='Find and organize relevant information from internet searches',
    backstory='''You are an expert internet researcher who excels at finding 
    accurate and relevant information online. You know how to formulate effective 
    search queries and analyze search results to provide valuable insights.''',
    tools=[get_search_results_tool],
    verbose=True,
    llm="gemini/gemini-1.5-flash"
)

# Create Search Task
search_task = Task(
    description='''Search for information about "latest AI developments 2025". 
    Find the most relevant and recent information available.''',
    expected_output='''A JSON-formatted list of search results including titles, 
    links, snippets, and sources for the most relevant information about 
    latest AI developments in 2025.''',
    agent=search_agent
)

def test_search_crew():
    """Test the search crew"""
    print("Search Tool Crew Test")
    print("=" * 30)
    
    # Create the crew
    search_crew = Crew(
        agents=[search_agent],
        tasks=[search_task],
        verbose=True,
        llm="gemini/gemini-1.5-flash"
    )
    
    # Execute the task
    result = search_crew.kickoff()
    
    print("\nFinal Search Result:")
    print("=" * 40)
    print(result)
    return result

def main():
    """Main function to test the search tool"""
    test_search_crew()

if __name__ == "__main__":
    main()