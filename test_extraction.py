#!/usr/bin/env python3

"""Test to debug the tool execution issue"""

import sys
import os
sys.path.append('.')

from utils.extraction import extract_tag_content

def test_extraction():
    """Test the XML tag extraction"""
    
    # Test case 1: Proper tool call format
    good_response = """<thought>I need to find hotels in London</thought>
<tool_call>{"name": "get_hotels_tool", "arguments": {"location": "London", "checkinDate": "2024-01-01", "checkoutDate": "2024-01-02", "max_items": 1}, "id": 0}</tool_call>"""
    
    # Test case 2: Model continuing with fake data (the problem case)
    bad_response = """<thought>I need to find hotels in London</thought>
<tool_call>{"name": "get_hotels_tool", "arguments": {"location": "London", "checkinDate": "2024-01-01", "checkoutDate": "2024-01-02", "max_items": 1}, "id": 0}</tool_call>

(Assume the above tool calls return the following data. In a real implementation, these would be fetched dynamically.)

{
  "0": {
    "hotels": [
      {"name": "Example Hotel", "booking_url": "https://example.com/hotel"}
    ]
  }
}

<response>
Here's a hotel for you: Example Hotel with booking at https://example.com/hotel
</response>"""
    
    print("=== Testing Good Response ===")
    thought = extract_tag_content(good_response, "thought")
    tool_calls = extract_tag_content(good_response, "tool_call")
    response = extract_tag_content(good_response, "response")
    
    print(f"Thought found: {thought.found}, content: {thought.content}")
    print(f"Tool calls found: {tool_calls.found}, content: {tool_calls.content}")
    print(f"Response found: {response.found}, content: {response.content}")
    
    print("\n=== Testing Bad Response (with simulation) ===")
    thought2 = extract_tag_content(bad_response, "thought")
    tool_calls2 = extract_tag_content(bad_response, "tool_call")
    response2 = extract_tag_content(bad_response, "response")
    
    print(f"Thought found: {thought2.found}, content: {thought2.content}")
    print(f"Tool calls found: {tool_calls2.found}, content: {tool_calls2.content}")
    print(f"Response found: {response2.found}, content: {response2.content}")
    
    # Check for simulation indicators
    simulation_indicators = ["assume", "example.com", "fake", "mock", "simulated"]
    has_simulation = any(indicator in bad_response.lower() for indicator in simulation_indicators)
    print(f"Contains simulation indicators: {has_simulation}")

if __name__ == "__main__":
    test_extraction()
