import os
import google.generativeai as genai
import requests
from PIL import Image
from io import BytesIO

from tool_decorator import tool

from dotenv import load_dotenv
import json

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY_ijyaan"))

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
        image_url (str): A URL pointing to an image of the location or landmark.

    Returns:
        str: JSON string containing AI-generated recommendations with descriptions, 
             suggested activities, and relevant contextual details.
    """
    try:
        # Use Gemini model that supports image input
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Fetch the image data from the URL
        response = requests.get(image_url)
        response.raise_for_status()
        
        # Open the image from the fetched bytes
        img = Image.open(BytesIO(response.content))
        
        # Generate content by passing the query and image to the model
        api_response = model.generate_content([query, img])
        
        result = {
            "message": {
                "content": api_response.text
            }
        }

        print(result)
        return json.dumps(result)

    except requests.exceptions.RequestException as e:
        error_msg = f"Error fetching image from URL: {e}"
        print(error_msg)
        return json.dumps({"error": error_msg})
    except Exception as e:
        error_msg = f"Error occurred: {e}"
        print(error_msg)
        return json.dumps({"error": error_msg})


if __name__ == "__main__":
    # Example usage
    query = "Describe this picture in a few sentences."
    image_url = "https://i.ibb.co/LD13KjW9/andy-holmes-D6-Tq-Ia-t-WRY-unsplash-jpg.jpg"
    print(get_multimodal_capability(query, image_url))