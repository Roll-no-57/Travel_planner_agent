import json
import requests
from tool_decorator import tool
from dotenv import load_dotenv
import os

load_dotenv()

#  lightweight scraping tool without summarization
@tool
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

