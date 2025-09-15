# Travel Planner Agent

A conversational, tool-using travel planning agent that builds structured trip itineraries, finds hotels and activities, fetches relevant images, and can generate travel blogs. It exposes both:

- An interactive CLI experience (`main.py`)
- A Flask HTTP API (`app.py`) suitable for containerized deployment

The agent follows a ReAct-style loop (Thought → Action → Observation → Response) and calls real tools for data instead of hallucinating.


## Features
- Trip planning with structured JSON itineraries (cities, daily activities, accommodations, overview images, costs).
- Real tool calls for data:
  - Hotels and activities via Apify (TripAdvisor data).
  - Image search via Serper (Google Images API).
  - Weather lookups via an external weather microservice.
  - Optional multimodal analysis of user-provided images via Hugging Face Inference API.
- Fallback response if the LLM returns invalid JSON (`fall_back_res.txt`).
- Flask API endpoints for programmatic access, including a simple travel blog generator.
- Dockerfile, docker-compose, Render config, and Cloud Build pipeline for deployment.


## Repository Structure
- `main.py`: Interactive CLI for planning trips end-to-end.
- `app.py`: Flask app exposing `/travel`, `/blog-generator`, and `/health` endpoints.
- `Trip_planner_agent.py`: High-level trip planning agent that orchestrates tools and response parsing.
- `Planning_agent.py`: Core ReAct loop implementation (`ReactAgent`) with tool execution.
- `Blog_generator_agent.py`: Image-aware, markdown travel blog generator using the multimodal tool.
- `Tools/`: Concrete tools the agent can call.
  - `get_hotels_tool.py`: Hotels via Apify TripAdvisor actor.
  - `get_activity_tool.py`: Attractions/restaurants via Apify TripAdvisor actor.
  - `image_search_tool.py`: Image URLs via Serper Images API.
  - `weather_tool.py`: Weather via external microservice.
  - `web_search_tool.py`, `web_scrape_tool.py`, `place_search_tool.py`: Search/scrape utilities (not all enabled by default).
  - `vision_capability_tool.py`: Multimodal image analysis via Hugging Face Inference API.
- `utils/`: Prompting, completions, and parsing helpers.
  - `completions.py`: Provider-agnostic completion wrapper for Gemini/Groq.
  - `extraction.py`: Helper to extract `<thought>`, `<tool_call>`, `<response>` tags.
  - `logging.py`: Fancy console formatting utilities.
- `tool_decorator.py`: Lightweight tool abstraction and argument validation.
- `fall_back_res.txt`: Prebuilt fallback trip-plan JSON used when the LLM output cannot be parsed.
- `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `render.yaml`, `cloudbuild.yaml`, `startup.sh`.
- `test_startup.py`: Placeholder used by the container startup script.


## How It Works

### ReAct Agent Flow
`Planning_agent.py` defines `ReactAgent`, which enforces a strict I/O contract with the model:
- The system prompt describes the available tools and the required XML tags:
  - `<thought>`: Agent reasoning
  - `<tool_call>`: JSON describing the tool invocation; the agent must stop after emitting this
  - `<observation>`: Injected by the system after the tool executes
  - `<response>`: Final natural-language or JSON answer
- The loop runs up to `max_rounds`, each time:
  1. Generate a completion.
  2. If `<response>` is present → return it as final.
  3. If `<tool_call>` is present → validate, execute the real tool, append `<observation>…</observation>` to the chat, and continue.
  4. If output format is wrong → inject guidance to correct the format and loop again.

The wrapper in `utils/completions.py` supports both Gemini and Groq providers. It adds stop words and post-processes to prevent the LLM from simulating tool outputs.

### Trip Planning Orchestration
`Trip_planner_agent.py` defines `TripPlanningAgent` with a focused system prompt and default tools:
- `get_image_search_results_tool` (images for the overview) – must return at least 3 URLs.
- `get_hotels_tool` (hotel details)
- `get_activity_tool` (attractions, activities, restaurants)
- `get_multimodal_capability` (optional; used if user provides an image URL)
- `get_weather_info` (used for weather-related intents)

`process_trip_query()`:
- Builds an enhanced prompt that reinforces tool usage and JSON output constraints.
- Runs the ReAct loop (`max_rounds=25`).
- Attempts to parse valid JSON from the model response. If parsing fails, it loads the fallback JSON from `fall_back_res.txt` and updates `sessionId`/`timestamp`.
- On error, returns a structured error response with an empty itinerary.

The expected trip-plan JSON structure includes:
- `itinerary.overview`: start/destination, dates, duration, people, cost estimate, and overview `image_urls`.
- `itinerary.Cities[]`: each with `travel`, `Accomodation` (with `image_urls`), and `days[]` containing `activities[]`.

### Blog Generation
`Blog_generator_agent.py` uses only the multimodal tool to analyze user-provided images and writes a structured, markdown blog. It returns JSON with `blog_content` and `metadata`. If parsing fails, it returns a structured fallback.


## Requirements
- Python 3.10+
- Accounts/keys for external services you intend to use:
  - Gemini API (Google Generative AI) and/or Groq API (optional; choose one provider).
  - Apify API (for TripAdvisor actor).
  - Serper API (for Google search/images).
  - Hugging Face Inference API (for multimodal).
  - Optional weather microservice URL (defaults to a hosted demo).


## Environment Variables
Create a `.env` file in the project root or export variables in your shell.

Minimum for Gemini provider (default):
- `GEMINI_API_KEY`: Your Google Generative AI key.

Optional to switch providers to Groq:
- `LLM_PROVIDER=groq`
- `GROQ_API_KEY`: Your Groq key
- `LLM_MODEL`: A Groq-supported model name (e.g., `llama-3.3-70b-versatile`)

Tools:
- `APIFY_API_TOKEN`: Required for `get_hotels_tool` and `get_activity_tool`.
- `SERPER_API_KEY`: Required for `get_image_search_results_tool`, `get_search_results_tool`, `get_raw_website_content_tool`, `get_place_search_results_tool`.
- `HF_TOKEN`: Required for `get_multimodal_capability`.
- `WEATHER_AGENT_API_URL`: Optional; defaults to `https://weather-agent-xhzk.onrender.com/weather`.

Server/runtime:
- `LLM_MODEL`: Defaults to `gemini-1.5-flash` in `app.py`; CLI uses `gemini-2.0-flash-exp` by default.
- `PORT`: Defaults to 8080 for server/containers.

Note: `Tools/weather_tool.py` sets a `GEMINI_API_KEY` value in code. You should override this by defining your own `GEMINI_API_KEY` in the environment before starting the app, and avoid committing secrets.


## Installation
- Ensure Python 3.10+ is installed.
- From the repo root:
  - `pip install -r requirements.txt`
  - Create `.env` with the variables you need (see above).

Example `.env` template:
```
# Core LLM (Gemini default)
GEMINI_API_KEY=your_gemini_key
LLM_MODEL=gemini-1.5-flash
# LLM_PROVIDER=groq
# GROQ_API_KEY=your_groq_key

# Tools
APIFY_API_TOKEN=your_apify_token
SERPER_API_KEY=your_serper_key
HF_TOKEN=your_hf_token
# WEATHER_AGENT_API_URL=https://your-weather-service/weather
```


## Running

### CLI (Interactive)
- `python main.py`
- Follow the prompts and type natural requests (e.g., “Plan a 5-day trip to Japan in March for 2 people”).
- Type `help` to see examples, `exit` to quit.

### Flask API (Local)
- `python app.py`
- Service binds to `0.0.0.0:$PORT` (default 5000 when run via `python app.py`, 8080 in containers).

Endpoints:
- `POST /travel`
  - Body: `{ "query": "Plan a 3-day trip to Rome in May for 2 people" }`
  - Response: `{ "response": { ...structured trip plan JSON... } }`
- `POST /blog-generator`
  - Body: `{ "tone": "casual", "language": "English", "creativity": "medium", "user_prompt": "Weekend in Lisbon", "user_images": ["https://..."] }`
  - Response: `{ "blog_content": {...}, "metadata": {...} }`
- `GET /health`
  - Response: `{ "status": "healthy" }`

cURL examples:
```
curl -X POST http://localhost:5000/travel \
  -H "Content-Type: application/json" \
  -d '{"query":"Plan a 4-day budget trip to Paris in June for 2"}'

curl -X POST http://localhost:5000/blog-generator \
  -H "Content-Type: application/json" \
  -d '{"tone":"friendly","language":"English","creativity":"medium","user_prompt":"Cherry blossom trip","user_images":["https://example.com/photo.jpg"]}'
```


## Docker

Build and run with Docker directly:
```
docker build -t travel-planner-agent .
docker run --rm -p 8080:8080 \
  --env-file .env \
  -e PORT=8080 \
  travel-planner-agent
```

Using docker-compose:
```
docker-compose up --build
```
The service exposes `http://localhost:8080`. Health checks hit `/health`.

`startup.sh` runs a basic startup test (`test_startup.py`) and launches Gunicorn with sensible defaults.


## Deployment

- Render: `render.yaml` sets up a Python web service using Gunicorn with environment variable placeholders.
- Google Cloud Build + Cloud Run: `cloudbuild.yaml` builds, pushes, and deploys to Cloud Run with common flags.

Provide the required environment variables in your platform’s secret manager or dashboard. Do not commit secrets.


## Tool Details and Notes

- `get_hotels_tool(location, checkinDate, checkoutDate, max_items=1)`
  - Apify actor `dbEyMBriog95Fv8CW` (TripAdvisor) with hotels enabled; returns JSON with basic hotel details and up to 3 `image_urls`.
- `get_activity_tool(location, max_items=3)`
  - Same Apify actor with attractions/restaurants enabled; returns activities with geo, rating, and up to 3 `image_urls`.
- `get_image_search_results_tool(query, max_results=5)`
  - Serper Images API; returns a JSON with `results` = list of image URLs.
  - Trip planning requires at least 3 valid URLs for overview images.
- `get_weather_info(query)`
  - Posts `{ query }` to `WEATHER_AGENT_API_URL` and returns a short text summary.
- `get_multimodal_capability(query, image_url)`
  - Uses Hugging Face InferenceClient (provider `novita`, model `zai-org/GLM-4.5V`) to analyze an image + text query.

The system prompt in `Trip_planner_agent.py` enforces:
- No hallucinations or placeholders.
- Always use the specified tools for each data type.
- Strict JSON output format for trip plans.


## Troubleshooting
- Missing keys or HTTP 4xx/5xx from external APIs
  - Ensure `.env` contains valid values and that you have API quota.
- “GEMINI_API_KEY not set” or provider errors
  - Default provider is Gemini; set `GEMINI_API_KEY` or switch to Groq with `LLM_PROVIDER=groq` and `GROQ_API_KEY`.
- Invalid JSON in responses
  - The agent retries format guidance; if still invalid, a structured fallback is returned from `fall_back_res.txt`.
- Strange characters in CLI output
  - Some decorative characters may render oddly on certain terminals; functionality is unaffected.
- Weather tool API URL
  - Override `WEATHER_AGENT_API_URL` to your own service if the default demo is unavailable.


## Development Notes
- Add or remove tools by editing `Trip_planner_agent.py` tool list.
- Tool schema is auto-derived from Python annotations via `@tool` decorator in `tool_decorator.py`.
- When adding tools, ensure they return JSON-serializable strings and that their parameter types are annotated.
- The ReAct loop expects the LLM to strictly emit the XML tags; `Planning_agent.py` contains format guards and guidance.


## Security
- Keep API keys in environment variables or a secret manager.
- Do not commit `.env` or secrets.
- Consider rotating keys used in development. Note the hardcoded `GEMINI_API_KEY` assignment in `Tools/weather_tool.py`; prefer overriding via environment.


## License
No license file is included. Provide one if you plan to distribute.

