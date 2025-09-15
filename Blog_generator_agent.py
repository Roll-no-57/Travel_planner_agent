from Planning_agent import ReactAgent
from colorama import Fore
import json
from datetime import datetime

from Tools.vision_capability_tool import get_multimodal_capability


class BlogGeneratorAgent:
    """
    Simple travel blog generator that analyzes only user-provided images
    and composes a markdown blog without web search or scraping.
    """

    def __init__(self, model: str = "gemini-2.0-flash-exp", provider=None):
        # Only the multimodal image analysis tool
        self.tools = [get_multimodal_capability]

        self.system_prompt = """
You are a focused travel blog writer. Create clear, engaging, well-structured travel blogs in markdown.

SCOPE AND DATA SOURCES
- Use only the user's prompt and provided image URLs.
- Analyze images via get_multimodal_capability to infer scenes, objects, moods, or activities.
- Do not perform web search or scraping. Avoid unverifiable specifics.

BLOG GUIDELINES
- Structure: title, intro, 3-6 concise sections, and a short wrap-up.
- Tone: follow the requested tone; keep language natural and helpful.
- Include the provided images at relevant points with descriptive alt text and short captions.
- Use markdown headings (#, ##, ###), lists (-), quotes (>), and **bold** for emphasis when useful.
- Use real blank lines; never output literal "\\n" characters.

IMAGE INTEGRATION
- For each provided image URL, call get_multimodal_capability with a helpful query and the URL.
- Use the tool's observation to write 1-2 sentences about the image and place it near the most relevant section.
- Embed with: ![Alt text](image_url "Short caption")

OUTPUT FORMAT (MUST be valid JSON):
{
    "blog_content": {
        "title": "Cherry Blossoms in Japan: A Magical Journey",
        "Detail": "Full markdown blog content with images embedded",
    },
    "metadata": {
        "word_count": 1250,
        "reading_time": "5 minutes",
        "generated_at": "2024-03-15T10:30:00Z"
    }
}

RULES
- Do not fabricate specific facts, prices, or schedules.
- Do not use web search or scrape any site.
- Keep it readable and useful without external references.
"""

        # Initialize the ReAct agent
        self.agent = ReactAgent(
            tools=self.tools,
            model=model,
            system_prompt=self.system_prompt,
            provider=provider,
        )

    def process_blog_query(self, query_data: dict) -> dict:
        """
        Process a blog generation query and return a comprehensive blog.

        Args:
            query_data: Dictionary containing:
                - tone: Writing tone (e.g., professional, casual)
                - language: Target language for the blog
                - creativity: Creativity level (low, medium, high)
                - user_prompt: Main topic or specific blog request
                - user_images: List of user-uploaded image URLs (optional)

        Returns:
            dict: The structured blog response with markdown content
        """
        try:
            tone = query_data.get('tone', 'casual')
            language = query_data.get('language', 'English')
            creativity = query_data.get('creativity', 'medium')
            user_prompt = query_data.get('user_prompt', '')
            user_images = query_data.get('user_images', [])

            enhanced_query = f"""
BLOG GENERATION REQUEST

Tone: {tone}
Language: {language}
Creativity Level: {creativity}
Main Topic/Prompt: {user_prompt}
User Images: {user_images if user_images else "None"}

INSTRUCTIONS
- Write a well-structured markdown blog in the specified tone and language.
- Do NOT use web search or scraping. Keep content general and observational.
- For EACH image URL provided, call get_multimodal_capability with a short, helpful query like
  "Describe the scene, key objects, activities, ambiance, and travel context" and the image_url.
- Use each observation to: (1) craft a one-sentence caption, (2) produce descriptive alt text,
  and (3) decide the most relevant section to place the image.
- Embed images with: ![Alt text](image_url "Short caption").
- Keep sections focused and concise; avoid unverifiable specifics.
- Return ONLY the required JSON with fields: blog_content, metadata, message, timestamp.
"""

            response = self.agent.run(enhanced_query, max_rounds=15)

            try:
                if isinstance(response, str):
                    start_idx = response.find('{')
                    end_idx = response.rfind('}')
                    if start_idx != -1 and end_idx != -1:
                        json_str = response[start_idx:end_idx+1]
                        parsed_response = json.loads(json_str)
                        return parsed_response

                return self._create_fallback_response(query_data, response)

            except json.JSONDecodeError:
                return self._create_fallback_response(query_data, response)

        except Exception as e:
            return self._create_error_response(query_data, str(e))

    def _create_fallback_response(self, query_data: dict, agent_response: str) -> dict:
        """Create a fallback response when agent output is not valid JSON."""
        return {
            "blog_content": f"""# Travel Blog

{agent_response}

---
*This blog was generated based on your request. For the best experience, please ensure all required information is provided.*
""",
            "metadata": {
                "title": "Generated Travel Blog",
                "tone": query_data.get('tone', 'casual'),
                "language": query_data.get('language', 'English'),
                "creativity_level": query_data.get('creativity', 'medium'),
                "word_count": len(agent_response.split()) if isinstance(agent_response, str) else 0,
                "reading_time": f"{max(1, (len(agent_response.split()) if isinstance(agent_response, str) else 0) // 200)} minutes",
                "tags": ["travel", "blog", "generated"],
                "destinations": []
            },
            "message": "Blog generated successfully using fallback formatting.",
            "timestamp": datetime.now().isoformat()
        }

    def _create_error_response(self, query_data: dict, error: str) -> dict:
        """Create an error response."""
        return {
            "blog_content": f"""# Blog Generation Error

We encountered an issue while generating your travel blog:

**Error**: {error}

Please try again with your request, ensuring all required information is provided.

## Tips for Better Blog Generation:
- Provide a clear topic or destination
- Specify your preferred tone and language
- Optionally include a few image URLs

---
*Please contact support if this error persists.*
""",
            "metadata": {
                "title": "Blog Generation Error",
                "tone": query_data.get('tone', 'casual'),
                "language": query_data.get('language', 'English'),
                "creativity_level": query_data.get('creativity', 'medium'),
                "word_count": 0,
                "reading_time": "1 minute",
                "tags": ["error"],
                "destinations": []
            },
            "message": f"Error occurred during blog generation: {error}",
            "timestamp": datetime.now().isoformat()
        }


def create_blog_agent(model: str = "gemini-2.0-flash-exp", provider=None) -> BlogGeneratorAgent:
    """Factory to create the simplified BlogGeneratorAgent."""
    print(Fore.GREEN + "Blog Agent Model used:", Fore.YELLOW + model)
    if provider:
        print(Fore.GREEN + "Provider:", Fore.YELLOW + str(provider))
    return BlogGeneratorAgent(model=model, provider=provider)

