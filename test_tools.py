#!/usr/bin/env python3

"""Test script to verify tools are working"""

import sys
sys.path.append('.')

from Tools.get_hotels_tool import get_hotels_tool
from Tools.get_activity_tool import get_activity_tool

def test_hotels_tool():
    print("Testing hotels tool...")
    try:
        result = get_hotels_tool('London', '2024-01-01', '2024-01-02', 1)
        print(f"Hotels tool result: {result}")
        return True
    except Exception as e:
        print(f"Hotels tool error: {e}")
        return False

def test_activity_tool():
    print("\nTesting activity tool...")
    try:
        result = get_activity_tool('London', 1)
        print(f"Activity tool result: {result}")
        return True
    except Exception as e:
        print(f"Activity tool error: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Tools ===")
    
    hotels_ok = test_hotels_tool()
    activity_ok = test_activity_tool()
    
    print(f"\n=== Results ===")
    print(f"Hotels tool: {'OK' if hotels_ok else 'FAILED'}")
    print(f"Activity tool: {'OK' if activity_ok else 'FAILED'}")
