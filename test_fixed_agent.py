#!/usr/bin/env python3

"""Test the fixed trip planning agent"""

import sys
import os
sys.path.append('.')

from Trip_planner_agent import TripPlanningAgent
import json

def test_trip_agent():
    """Test the trip planning agent with tool execution"""
    
    print("=== Testing Fixed Trip Planning Agent ===")
    
    try:
        # Create the agent
        agent = TripPlanningAgent(model="gemini-2.0-flash-exp")
        print("✅ Agent created successfully")
        
        # Test with a simple query
        query = "Plan a 1-day trip to London from Bangladesh for 2 people on a low budget"
        session_id = "test_session_123"
        
        print(f"\n🔍 Query: {query}")
        print(f"🆔 Session: {session_id}")
        
        # Process the query
        result = agent.process_trip_query(query, session_id)
        
        print("\n📋 Result:")
        print(json.dumps(result, indent=2)[:1000] + "..." if len(str(result)) > 1000 else json.dumps(result, indent=2))
        
        # Check if real tools were used
        if "example.com" in str(result):
            print("\n❌ STILL USING FAKE DATA!")
        else:
            print("\n✅ No fake URLs detected")
            
        # Check if we have an itinerary
        if "itinerary" in result and result["itinerary"]:
            print("✅ Itinerary generated")
        else:
            print("❌ No itinerary generated")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_trip_agent()
