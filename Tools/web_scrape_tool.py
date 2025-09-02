import json
import requests
from crewai.tools import tool
from crewai import Agent, Task, Crew
from dotenv import load_dotenv
import os

load_dotenv()

#  lightweight scraping tool without summarization
@tool("get_raw_website_content")
def get_raw_website_content_tool(website: str) -> str:
    """
    Scrape website content using Serper and return raw text without summarization.
    Useful for getting full content when you need all details.
    
    Args:
        website: The website URL to scrape (e.g., "https://example.com")
    """
    try:
        # Get the Serper API key from environment variables
        serper_api_key = os.getenv("SERPER_API_KEY")
        if not serper_api_key:
            return "Error: SERPER_API_KEY not found in environment variables"
        
        # Scrape website content using Serper
        url = "https://scrape.serper.dev"
        payload = json.dumps({"url": website})
        headers = {
            'X-API-KEY': serper_api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, data=payload)
        
        if response.status_code != 200:
            return f"Error: Failed to scrape website. Status code: {response.status_code}"
        
        # Parse and return the response
        scrape_data = response.json()
        
        result = {
            "website": website,
            "status": "success",
            "title": scrape_data.get('title', 'No title found'),
            "description": scrape_data.get('description', 'No description found'),
            "content": scrape_data.get('text', scrape_data.get('content', 'No content found')),
            "url": scrape_data.get('url', website)
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return f"Error while scraping website: {str(e)}"


# ======================================== For testing purpose ======================================================

# Create Website Content Agent
website_agent = Agent(
    role='Website Content Analyzer',
    goal='Scrape and analyze website content to extract valuable information',
    backstory='''You are a web content specialist who excels at extracting and 
    organizing information from websites using modern scraping services. You provide 
    clear, structured summaries of web content for research and analysis purposes.''',
    tools=[get_raw_website_content_tool],
    verbose=True,
    llm="gemini/gemini-1.5-flash"
)

# Create Website Analysis Task
website_task = Task(
    description='''Scrape and analyze the content from https://www.viator.com/blog/Dhaka/d22495/How-to-Spend-2-Days-in-Dhaka/i29091. 
    Extract the key information and provide a comprehensive summary of the travel guide content.''',
    expected_output='''A JSON-formatted summary of the website content including 
    key information about spending 2 days in Dhaka, main attractions, recommendations,
    and important travel details organized by sections.''',
    agent=website_agent
)

def test_website_crew():
    """Test the website scraping crew"""
    print("Serper Website Scraping Crew Test")
    print("=" * 40)
    
    # Create the crew
    website_crew = Crew(
        agents=[website_agent],
        tasks=[website_task],
        verbose=True,
        llm="gemini/gemini-1.5-flash"
    )
    
    # Execute the task
    result = website_crew.kickoff()
    
    print("\nFinal Website Analysis Result:")
    print("=" * 40)
    print(result)
    return result

def main():
    """Main function to test the website tool"""
    test_website_crew()

if __name__ == "__main__":
    main()