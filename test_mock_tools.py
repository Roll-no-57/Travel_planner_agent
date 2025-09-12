#!/usr/bin/env python3

"""Test with mock tools to isolate the issue"""

import sys
import os
sys.path.append('.')

from tool_decorator import tool

# Create a simple mock tool for testing
@tool
def mock_hotel_tool(location: str, checkinDate: str, checkoutDate: str, max_items: int = 1) -> str:
    """Mock hotel search tool for testing"""
    return '{"hotels": [{"name": "Test Hotel", "booking_url": "https://realhotel.com/book"}]}'

@tool  
def mock_activity_tool(location: str, max_items: int = 3) -> str:
    """Mock activity search tool for testing"""
    return '{"activities": [{"name": "Test Museum", "booking_url": "https://realmuseum.com/tickets"}]}'

def test_with_mock_tools():
    """Test the ReAct agent with mock tools"""
    
    print("=== Testing with Mock Tools ===")
    
    try:
        from Planning_agent import ReactAgent
        
        # Create agent with mock tools
        tools = [mock_hotel_tool, mock_activity_tool]
        
        system_prompt = """You are a trip planning assistant. Use the available tools to find hotels and activities. NEVER create fake data - only use real tool results."""
        
        agent = ReactAgent(
            tools=tools,
            model="gemini-2.0-flash-exp",
            system_prompt=system_prompt
        )
        
        print("✅ Agent created with mock tools")
        print(f"Available tools: {[tool.name for tool in agent.tools]}")
        
        # Simple query
        query = "Find me a hotel in London for January 1-2, 2024"
        print(f"\n🔍 Query: {query}")
        
        result = agent.run(query, max_rounds=5)
        print(f"\n📋 Result: {result}")
        
        # Check for simulation indicators
        if any(indicator in result.lower() for indicator in ["assume", "example.com", "fake", "mock"]):
            print("❌ Still contains simulation indicators")
        else:
            print("✅ No simulation detected")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_with_mock_tools()
