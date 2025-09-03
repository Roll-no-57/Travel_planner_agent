import requests
from crewai.tools import tool
from crewai import Agent, Task, Crew
import os
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Set your Gemini API key
os.environ["GEMINI_API_KEY"] = "AIzaSyCS4NPTf-t8SUtXnDSrglj_Vmj2Gl1yv9o"

@tool("weather_info")
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







#=======================================FOR testing tool===========================================





# Create a Weather Agent
weather_agent = Agent(
    role='Weather Specialist',
    goal='Provide accurate and helpful weather information to users',
    backstory='''You are a knowledgeable weather specialist who can provide 
    detailed weather information for any location. You understand weather patterns, 
    can interpret forecasts, and always provide helpful weather-related advice.''',
    tools=[get_weather_info],
    verbose=True,
    llm="gemini/gemini-1.5-flash"
)

# Create a Weather Task
weather_task = Task(
    description='''Get the weather information of the day after in Dhaka. Include any additional 
    weather details that might be useful for planning outdoor activities.''',
    expected_output='''A comprehensive weather report for Dhaka on the day after, 
    specifically addressing rain probability and including practical advice 
    for outdoor activities.''',
    agent=weather_agent
)

# Create and run the Crew
def main():
    """Main function to execute the weather crew"""
    
    # Test the API health first
    try:
        health_response = requests.get("https://weather-agent-xhzk.onrender.com/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Weather API is healthy!")
            print(f"Status: {health_response.json()}")
        else:
            print("⚠️ Weather API health check failed")
    except Exception as e:
        print(f"❌ Could not reach weather API: {e}")
    
    # Create the crew with Gemini model
    weather_crew = Crew(
        agents=[weather_agent],
        tasks=[weather_task],
        verbose=True,
        llm="gemini/gemini-2.0-flash",
        memory=True,
        embedder={
            "provider": "google",
            "config": {
                "api_key": "AIzaSyCS4NPTf-t8SUtXnDSrglj_Vmj2Gl1yv9o",
                "model": "text-embedding-004"  # or "text-embedding-preview-0409"
            }
        }
    )
    
    # Execute the task
    print("\n🚀 Starting weather crew...")
    result = weather_crew.kickoff()
    
    print("\n📋 Final Result:")
    print("=" * 50)
    print(result)
    return result

if __name__ == "__main__":
    main()