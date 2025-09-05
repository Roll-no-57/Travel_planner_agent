from flask import Flask, request, jsonify
from Trip_planner_agent import create_trip_agent
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

agent = create_trip_agent(model="gemini-2.0-flash-exp")

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
        print(f"[RESPONSE] /travel | response: {response}")
        return jsonify({"response": response})
    except Exception as e:
        print(f"[RESPONSE] /travel | error: {str(e)}")
        return jsonify({"error": f"Error processing query: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    print("Health check endpoint called")
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))  # Render provides PORT
    app.run(debug=True, host='0.0.0.0', port=port)
