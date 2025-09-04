import os
from huggingface_hub import InferenceClient

from tool_decorator import tool

from dotenv import load_dotenv
import json

load_dotenv()

@tool
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

