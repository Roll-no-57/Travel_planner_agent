from Trip_planner_agent import create_trip_agent
import sys
import json
from colorama import Fore, Style, init

# Initialize colorama for colored output
init()

def print_welcome():
    """Print welcome message with examples."""
    print(Style.BRIGHT + Fore.CYAN + "="*60)
    print(Fore.MAGENTA + "✈️  Welcome to the Intelligent Trip Planning Agent! ✈️")
    print(Style.BRIGHT + Fore.CYAN + "="*60)
    print(Fore.WHITE + "\nI can help you plan amazing trips with queries like:")
    print(Fore.YELLOW + "• 'Plan a 5-day trip to Europe for 2 people'")
    print(Fore.YELLOW + "• 'I want to visit Japan for a week in March'")
    print(Fore.YELLOW + "• 'Best places to visit in Southeast Asia'")
    print(Fore.YELLOW + "• 'Romantic getaway for 3 days under $2000'")
    print(Fore.YELLOW + "• 'Adventure trip to New Zealand'")
    print(Fore.YELLOW + "• 'Family vacation to Disney World'")
    print(Fore.YELLOW + "• 'Backpacking through South America'")
    
    print(Fore.GREEN + "\nWhat I'll provide:")
    print(Fore.GREEN + "🏨 Best accommodations for each destination")
    print(Fore.GREEN + "🎯 Top activities and attractions")
    print(Fore.GREEN + "🗺️  Detailed daily itineraries")
    print(Fore.GREEN + "💰 Cost estimates and travel options")
    print(Fore.GREEN + "📍 Locations with coordinates")
    
    print(Fore.WHITE + "\nType 'exit', 'quit', or 'bye' to end the conversation.")
    print(Fore.WHITE + "Type 'help' to see this message again.")
    print(Style.BRIGHT + Fore.CYAN + "="*60 + "\n")


def print_help():
    """Print help information."""
    print(Fore.CYAN + "\n📖 Trip Planning Agent Help:")
    print(Fore.WHITE + "Here are some example queries you can try:")
    
    examples = [
        "Destination-based: 'Plan a trip to Italy for 7 days'",
        "Budget-focused: 'European trip under $3000 for 2 people'", 
        "Theme-based: 'Adventure trip with hiking and water sports'",
        "Duration-specific: 'Weekend getaway from New York'",
        "Group travel: 'Family trip with kids to California'",
        "Season-specific: 'Best places to visit in winter'",
        "Activity-focused: 'Food and culture tour of Asia'",
        "Multi-city: 'Tokyo, Kyoto, and Osaka in 10 days'"
    ]
    
    for i, example in enumerate(examples, 1):
        print(Fore.YELLOW + f"{i}. {example}")
    
    print(Fore.GREEN + "\nThe agent will automatically:")
    print(Fore.GREEN + "1. Search for the best destinations")
    print(Fore.GREEN + "2. Find top accommodations in each city")
    print(Fore.GREEN + "3. Discover activities and attractions")
    print(Fore.GREEN + "4. Create a detailed itinerary with all information\n")


def format_trip_response(response_data):
    """Format the trip planning response for better readability."""
    try:
        print(Fore.GREEN + "\n" + "="*60)
        print(Fore.MAGENTA + "🎯 YOUR TRIP PLAN")
        print(Fore.GREEN + "="*60)
        
        # Display main message
        print(Fore.CYAN + "\n📝 " + response_data.get("message", "Trip plan created successfully!"))
        
        # Display overview
        overview = response_data.get("itinerary", {}).get("overview", {})
        if overview:
            print(Fore.YELLOW + f"\n🗺️  TRIP OVERVIEW:")
            print(Fore.WHITE + f"   📍 From: {overview.get('start_location', 'N/A')}")
            print(Fore.WHITE + f"   🎯 To: {overview.get('destination_location', 'N/A')}")
            print(Fore.WHITE + f"   📅 Duration: {overview.get('duration_days', 0)} days")
            print(Fore.WHITE + f"   👥 People: {overview.get('people_count', 1)}")
            print(Fore.WHITE + f"   💰 Estimated Cost: ${overview.get('Estimated_overall_cost', 0)}")
            print(Fore.WHITE + f"   📆 Dates: {overview.get('start_date', 'TBD')} to {overview.get('end_date', 'TBD')}")
        
        # Display cities and itinerary
        cities = response_data.get("itinerary", {}).get("Cities", [])
        for i, city in enumerate(cities, 1):
            print(Fore.CYAN + f"\n🏙️  DESTINATION {i}")
            
            # Accommodation
            accommodation = city.get("Accomodation", {})
            if accommodation.get("name"):
                print(Fore.YELLOW + f"   🏨 HOTEL: {accommodation.get('name', 'N/A')}")
                print(Fore.WHITE + f"      📍 {accommodation.get('address', 'N/A')}")
                print(Fore.WHITE + f"      ⭐ Rating: {accommodation.get('rating', 0)}/5 ({accommodation.get('review_count', 0)} reviews)")
                
                price = accommodation.get("price", {})
                if price.get("amount"):
                    print(Fore.WHITE + f"      💰 Price: ${price.get('amount', 0)} {price.get('currency', 'USD')}")
            
            # Daily activities
            days = city.get("days", [])
            for day in days:
                print(Fore.GREEN + f"\n   📅 {day.get('day_number', 'Day')}: {day.get('title', 'Exploration Day')}")
                print(Fore.WHITE + f"      📝 {day.get('description', 'Discover the city')}")
                
                activities = day.get("activities", [])
                for j, activity in enumerate(activities, 1):
                    print(Fore.CYAN + f"      🎯 Activity {j}: {activity.get('title', 'N/A')}")
                    print(Fore.WHITE + f"         📍 {activity.get('address', 'N/A')}")
                    print(Fore.WHITE + f"         ⏰ Duration: {activity.get('minimum_duration', 'N/A')}")
                    if activity.get('Ratings'):
                        print(Fore.WHITE + f"         ⭐ Rating: {activity.get('Ratings', 0)}/5")
        
        print(Fore.GREEN + "\n" + "="*60)
        
    except Exception as e:
        print(Fore.RED + f"Error formatting response: {e}")
        # Fallback: print raw JSON
        print(Fore.CYAN + "\nRaw Response:")
        print(json.dumps(response_data, indent=2))


def main():
    """Main function to run the trip planning agent."""
    try:
        print_welcome()
        
        # Interactive loop
        while True:
            try:
                # Get user input
                print(Fore.BLUE + "🔄 Initializing Trip Planning Agent...")
                model = "gemini-2.0-flash-exp"
                agent = create_trip_agent(model)
                print(Fore.GREEN + "✅ Trip Planning Agent ready!\n")
                
                user_query = input(Fore.WHITE + Style.BRIGHT + "You: " + Style.RESET_ALL).strip()
                
                # Handle exit commands
                if user_query.lower() in ["exit", "quit", "bye", "q"]:
                    print(Fore.MAGENTA + "\n👋 Thanks for using Trip Planning Agent! Have an amazing trip!")
                    break
                
                # Handle help command
                if user_query.lower() in ["help", "h", "?"]:
                    print_help()
                    continue
                
                # Handle empty input
                if not user_query:
                    print(Fore.YELLOW + "Please tell me about your dream trip!")
                    continue
                
                # Process the trip planning query
                print(Fore.BLUE + "\n🤖 Trip Planning Agent: ", end="")
                print(Fore.CYAN + "Planning your amazing trip...")
                
                # Create request body format
                request_body = {
                    "message": user_query,
                    "sessionId": f"session_{sys.exc_info()[2] if sys.exc_info()[2] else 'default'}"
                }
                
                response = agent.process_trip_query(user_query, request_body["sessionId"])
                
                # Display formatted response
                if isinstance(response, dict):
                    format_trip_response(response)
                else:
                    print(Fore.GREEN + "🌟 Trip Planning Agent: " + Fore.WHITE + str(response) + "\n")
                
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  Interrupted by user. Goodbye!")
                break
            except Exception as e:
                print(Fore.RED + f"\n❌ Error processing query: {str(e)}")
                print(Fore.YELLOW + "Please try asking your question differently.\n")
    
    except Exception as e:
        print(Fore.RED + f"❌ Failed to initialize Trip Planning Agent: {str(e)}")
        print(Fore.YELLOW + "Please check your internet connection and API keys.")
        sys.exit(1)


if __name__ == "__main__":
    main()