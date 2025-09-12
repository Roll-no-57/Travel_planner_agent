#!/usr/bin/env python3

"""Test script to verify the ReAct agent tool execution"""

import sys
import os
sys.path.append('.')

from Planning_agent import ReactAgent
from Tools.get_hotels_tool import get_hotels_tool
from Tools.get_activity_tool import get_activity_tool

def test_react_agent():
    print("=== Testing ReAct Agent Tool Execution ===")
    
    # Create a simple agent with just one tool
    tools = [get_hotels_tool]
    
    system_prompt = """You are a travel planning assistant. Use the available tools to help plan trips."""
    
    try:
        agent = ReactAgent(
            tools=tools,
            model="gemini-2.0-flash-exp",  # or whatever model you're using
            system_prompt=system_prompt
        )
        
        print("Agent created successfully")
        print(f"Available tools: {[tool.name for tool in agent.tools]}")
        print(f"Tools dict keys: {list(agent.tools_dict.keys())}")
        
        # Test with a simple query
        query = "Find me one hotel in London for January 1-2, 2024"
        print(f"\nQuery: {query}")
        
        result = agent.run(query, max_rounds=3)
        print(f"\nResult: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_react_agent()
