#!/usr/bin/env python3

"""Test the basic API connection"""

import sys
import os
sys.path.append('.')

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def test_gemini_connection():
    """Test basic Gemini API connection"""
    
    print("=== Testing Gemini API Connection ===")
    
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ No GEMINI_API_KEY found")
            return False
            
        print(f"✅ API key found: {api_key[:10]}...")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        # Simple test
        response = model.generate_content("Hello, how are you?")
        print(f"✅ Response: {response.text}")
        
        # Test with tool format
        tool_test = """You must respond in XML format.

<thought>I need to respond to the user</thought>
<response>Hello! I'm doing well, thank you for asking.</response>"""
        
        response2 = model.generate_content("Respond using XML tags with thought and response tags.")
        print(f"✅ XML Response: {response2.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_gemini_connection()
