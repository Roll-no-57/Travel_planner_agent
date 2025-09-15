import os
from groq import Groq
import time
import requests
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
        query (str): A natural language request describing what the user wants like describes whats in the image
        image_url (str): A URL pointing to an image of the location or landmark.

    Returns:
        str: JSON string containing AI-generated recommendations with descriptions, 
             suggested activities, and relevant contextual details.
    """
    try:
        # Validate image URL first
        if not image_url or not image_url.startswith(('http://', 'https://')):
            return json.dumps({"error": "Invalid image URL provided"})
        
        # Check if image URL is accessible
        try:
            response = requests.head(image_url, timeout=10)
            if response.status_code not in [200, 301, 302]:
                return json.dumps({"error": f"Image URL not accessible. Status code: {response.status_code}"})
        except requests.RequestException as e:
            return json.dumps({"error": f"Cannot access image URL: {str(e)}"})

        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        # Retry logic for handling timeouts
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                print(f"Attempting multimodal analysis (attempt {attempt + 1}/{max_retries})...")
                
                completion = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": f"Analyze this image and answer: {query}. Please provide a detailed response about what you see in the image."},
                                {"type": "image_url", "image_url": {"url": image_url}},
                            ],
                        }
                    ],
                    temperature=0.7,  # Reduced for more consistent responses
                    max_completion_tokens=512,  # Reduced to prevent timeouts
                    top_p=0.9,
                    stream=False,
                    stop=None,
                )

                result = {
                    "message": completion.choices[0].message.content,
                    "status": "success",
                    "attempt": attempt + 1
                }

                print("Multimodal analysis successful!")
                return json.dumps(result)
                
            except Exception as api_error:
                error_message = str(api_error)
                print(f"Attempt {attempt + 1} failed: {error_message}")
                
                # Check if it's a timeout or rate limit error
                if "deadline exceeded" in error_message or "timeout" in error_message.lower():
                    if attempt < max_retries - 1:
                        print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        return json.dumps({
                            "error": "Request timed out after multiple attempts. The image might be too large or complex.",
                            "suggestion": "Try with a smaller image or simpler query."
                        })
                
                # For other errors, don't retry
                return json.dumps({
                    "error": f"API error: {error_message}",
                    "attempt": attempt + 1
                })

    except Exception as e:
        print(f"Error occurred: {e}")
        return json.dumps({
            "error": f"Unexpected error: {str(e)}",
            "suggestion": "Please check your API key and image URL."
        })

