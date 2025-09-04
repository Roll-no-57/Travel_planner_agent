import requests
from tool_decorator import tool
import os
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Set your Gemini API key
os.environ["GEMINI_API_KEY"] = "AIzaSyCS4NPTf-t8SUtXnDSrglj_Vmj2Gl1yv9o"

@tool
def get_weather_info(query: str) -> str:
    """
    Get weather information for any location or weather-related query.
    This tool can answer questions like 'Will it rain in Dhaka tomorrow?', 
    'What's the weather like in London?', etc.
    """
    try:
        # Your weather API endpoint
        url = os.getenv("WEATHER_AGENT_API_URL", "https://weather-agent-xhzk.onrender.com/weather")
        
        # Make POST request with the query
        response = requests.post(
            url,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=300
        )
        
        if response.status_code == 200:
            data = response.json()
            weather_response = data.get("response", "No weather information available")
            sentiment = data.get("sentiment", 0.0)
            
            return f"Weather Information: {weather_response} (Sentiment: {sentiment})"
        else:
            return f"Failed to get weather information. Status code: {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"





