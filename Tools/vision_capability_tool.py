import os
from huggingface_hub import InferenceClient

from crewai.tools import tool
from crewai import Agent, Task, Crew

from dotenv import load_dotenv
import json

load_dotenv()

@tool("get_vision_capability")
def get_multimodal_capability(query: str, image_url: str) -> str:
    """
    Generate multimodal travel recommendations (activities, attractions, dining options) 
    based on a user query and an image reference.

    This tool combines natural language input (query) with visual context (image_url) 
    to provide detailed travel insights such as must-visit attractions, great restaurants, 
    and unique experiences at the destination.

    Args:
        query (str): A natural language request describing what the user wants 
                     (e.g., "Plan a 2-day itinerary", "Find top attractions").
        image_url (str): A URL pointing to an image of the location or landmark.

    Returns:
        str: JSON string containing AI-generated recommendations with descriptions, 
             suggested activities, and relevant contextual details.
    """
    try:
        client = InferenceClient(
            provider="novita",
            api_key=os.getenv("HF_TOKEN"),
        )

        completion = client.chat.completions.create(
            model="zai-org/GLM-4.5V",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
        )

        result = {
            "message": completion.choices[0].message
        }

        print(result)
        return json.dumps(result)

    except Exception as e:
        print(f"Error occurred: {e}")
        return json.dumps({"error": str(e)})


# ========================= For Testing Purpose =========================

# Create Vision Capability Agent
multimodal_capability_agent = Agent(
    role="Travel Experience Curator",
    goal="Design immersive travel experiences by combining visual context with user requests.",
    backstory=(
        "You are a seasoned travel curator who specializes in planning memorable trips. "
        "By analyzing both images and user preferences, you recommend the best attractions, "
        "dining spots, and activities. You always return structured and helpful details, "
        "limited to the top 3 options per category."
    ),
    tools=[get_multimodal_capability],
    verbose=True,
    llm="gemini/gemini-1.5-flash"
)

# Create Activity Search Task
multimodal_capability_task = Task(
    description=(
        "Analyze the image of Lauterbrunnen, Switzerland and the user request. "
        "Return a curated set of top recommendations for attractions, restaurants, "
        "and unique activities. The response must combine cultural, natural, "
        "and dining highlights."
    ),
    expected_output=(
        "A JSON-formatted response with at least 3 curated recommendations. "
        "Each recommendation must include: title, description, category "
        "(attraction/restaurant/activity), address, coordinates if possible, "
        "and a representative image URL (\"https://upload.wikimedia.org/wikipedia/commons/2/29/1_lauterbrunnen_valley_wengen_2022.jpg\")."
    ),
    agent=multimodal_capability_agent
)

def test_activity_crew():
    """Run a test of the multimodal activity crew."""
    print("Multimodal Activity Crew Test")
    print("=" * 30)

    # Create the crew
    activity_crew = Crew(
        agents=[multimodal_capability_agent],
        tasks=[multimodal_capability_task],
        verbose=True,
        llm="gemini/gemini-1.5-flash"
    )

    # Execute the task
    result = activity_crew.kickoff()

    print("\nFinal Activity Search Result:")
    print("=" * 40)
    print(result)
    return result

def main():
    """Main function to test the activity tool."""
    test_activity_crew()

if __name__ == "__main__":
    main()
