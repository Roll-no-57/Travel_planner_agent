#!/usr/bin/env python3

"""Simple test to check if the tool system is working"""

import sys
import os
sys.path.append('.')

# Test if we can import and examine the tools
print("=== Testing Tool Imports ===")

try:
    from Tools.get_hotels_tool import get_hotels_tool
    print(f"Hotel tool imported: {type(get_hotels_tool)}")
    print(f"Hotel tool name: {get_hotels_tool.name}")
    print(f"Hotel tool fn: {get_hotels_tool.fn}")
    print(f"Hotel tool signature: {get_hotels_tool.fn_signature}")
    
    # Try to call the tool directly
    print("\n=== Testing Direct Tool Call ===")
    result = get_hotels_tool.run(location="London", checkinDate="2024-01-01", checkoutDate="2024-01-02", max_items=1)
    print(f"Direct call result: {result[:200]}...")  # First 200 chars
    
except Exception as e:
    print(f"Error with hotel tool: {e}")
    import traceback
    traceback.print_exc()

try:
    from Tools.get_activity_tool import get_activity_tool  
    print(f"\nActivity tool imported: {type(get_activity_tool)}")
    print(f"Activity tool name: {get_activity_tool.name}")
    
except Exception as e:
    print(f"Error with activity tool: {e}")
    import traceback
    traceback.print_exc()
