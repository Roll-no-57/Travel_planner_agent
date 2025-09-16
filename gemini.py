import google.generativeai as genai
import requests
from PIL import Image
from io import BytesIO
import os

# Set your API key from environment variables or replace directly
genai.configure(api_key="AIzaSyB88SeKIbJgoR3VMPThF_YEXLmdzxFcThs")

# Use a model that supports image input
model = genai.GenerativeModel('gemini-1.5-flash')

# 1. Define the URL of the image you want to use.
image_url = "https://i.ibb.co/LD13KjW9/andy-holmes-D6-Tq-Ia-t-WRY-unsplash-jpg.jpg" # Replace with your image URL

try:
    # 2. Fetch the image data from the URL.
    response = requests.get(image_url)
    response.raise_for_status() # Raise an exception for bad status codes
    
    # 3. Open the image from the fetched bytes.
    img = Image.open(BytesIO(response.content))
    
    # 4. Generate content by passing the image and text to the model.
    api_response = model.generate_content(["Describe this picture in a few sentences.", img])
    
    # 5. Print the model's response.
    print(api_response.text)
    
except requests.exceptions.RequestException as e:
    print(f"Error fetching image from URL: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
