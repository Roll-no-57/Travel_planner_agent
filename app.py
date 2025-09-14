from flask import Flask, request, jsonify
from Trip_planner_agent import create_trip_agent
from Blog_generator_agent import create_blog_agent
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Read provider and model from environment for easy switching (LLM_PROVIDER: gemini|groq)
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-1.5-flash")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER")  # optional
agent = create_trip_agent(model=LLM_MODEL, provider=LLM_PROVIDER)
blog_agent = create_blog_agent(model=LLM_MODEL, provider=LLM_PROVIDER)

@app.route('/travel', methods=['POST'])
def travel_query():
    data = request.json
    query = data.get('query')
    print(f"[REQUEST] /travel | query: {query}")
    if not query:
        print("[RESPONSE] /travel | error: No query provided")
        return jsonify({"error": "No query provided"}), 400
    try:
        response = agent.process_trip_query(query)
        print({"response": response})
        return jsonify({"response": response})
    except Exception as e:
        print({"error": f"Error processing query: {str(e)}"})
        return jsonify({"error": f"Error processing query: {str(e)}"}), 500

@app.route('/blog-generator', methods=['POST'])
def blog_generator():
    data = request.json
    print(f"[REQUEST] /blog-generator | data: {data}")
    
    # Validate required fields
    if not data:
        print("[RESPONSE] /blog-generator | error: No data provided")
        return jsonify({"error": "No data provided"}), 400
    
    # Extract and validate parameters
    query_data = {
        'tone': data.get('tone', 'casual'),
        'language': data.get('language', 'English'),
        'tour_itinerary': data.get('tour_itinerary', ''),
        'creativity': data.get('creativity', 'medium'),
        'user_prompt': data.get('user_prompt', ''),
        'user_images': data.get('user_images', [])
    }
    
    # Validate that at least user_prompt or tour_itinerary is provided
    if not query_data['user_prompt'] and not query_data['tour_itinerary']:
        print("[RESPONSE] /blog-generator | error: No topic or itinerary provided")
        return jsonify({"error": "Either 'user_prompt' or 'tour_itinerary' must be provided"}), 400
    
    try:
        response = blog_agent.process_blog_query(query_data)
        print(f"[RESPONSE] /blog-generator | success: Blog generated")
        return jsonify(response)
    except Exception as e:
        print(f"[RESPONSE] /blog-generator | error: {str(e)}")
        return jsonify({"error": f"Error generating blog: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    print("Health check endpoint called")
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))  # Render provides PORT
    app.run(debug=True, host='0.0.0.0', port=port)
