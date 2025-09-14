from Planning_agent import ReactAgent
from colorama import Fore, Style, init
import json
from datetime import datetime

from Tools.vision_capability_tool import get_multimodal_capability
from Tools.web_scrape_tool import get_raw_website_content_tool
from Tools.web_search_tool import get_search_results_tool


class BlogGeneratorAgent:
    """
    A comprehensive blog generator agent that can create detailed travel blogs
    using natural language processing and multiple data sources.
    """

    def __init__(self, model: str = "gemini-2.0-flash-exp", provider=None):
        """
        Initialize the Blog Generator Agent with necessary tools.
        Args:
            model: The LLM model to use for reasoning
            provider: 'gemini' or 'groq' (optional). If None, ReactAgent decides via env.
        """
        # Define blog generation tools
        self.tools = [
            # get_multimodal_capability,
            # get_raw_website_content_tool,
            # get_search_results_tool,
        ]
        self.system_prompt = """
You are a specialized travel blog writer and content creator. 
Your job is to create engaging, detailed, and well-structured travel blogs in markdown format.

...

=========================
BLOG CREATION GUIDELINES
=========================

1. **Content Structure**: Create comprehensive blogs with:
   - Compelling headlines and subheadings
   - Detailed paragraphs with rich descriptions
   - Practical travel tips and insights
   - Local culture and history information
   - Restaurant and accommodation recommendations
   - Transportation and logistics advice
   - Add image urls of user uploaded images in the blog where relevant in markdown format

2. **Markdown Formatting**:
   - Use real blank lines for spacing (DO NOT output literal "\\n\\n" inside markdown).
   - # for main title
   - ## for major sections
   - ### for subsections
   - **bold** for emphasis
   - *italic* for subtle emphasis
   - Lists with - or numbered lists
   - > for quotes or tips
   - Code blocks for practical information like addresses
   - Images must use this format:
     ![Alt text](image_url "Caption")

3. **Image Integration**:
   - Use user-uploaded images for personal experiences analysis
   - Find relevant web images for destinations, food, attractions
   - Include image descriptions and captions
   - Format: ![Alt text](image_url "Caption")

...

=========================
RESPONSE FORMAT
=========================

Always return a JSON response with this structure:
{
  "blog_content": "Full markdown blog content here. 
   Make sure markdown uses real blank lines, not escaped \\n characters. 
   For example:

   # Title

   Paragraph text here.

   ![Alt](url)

   ## Section

   More content...",
  "metadata": {
    "title": "Blog title",
    "tone": "requested tone",
    "language": "requested language", 
    "creativity_level": "requested creativity",
    "word_count": estimated_word_count,
    "reading_time": "estimated reading time in minutes",
    "tags": ["relevant", "travel", "tags"],
    "destinations": ["mentioned destinations"]
  },
  "message": "Brief summary of the created blog",
  "timestamp": "current ISO timestamp"
}

=========================
CRITICAL RULES
=========================
- NEVER hallucinate facts about destinations, prices, or specific details
- ALWAYS verify information using the web search and scrape tools
- Use get_multimodal_capability ONLY for user-uploaded images
- Create engaging, readable content that provides real value
- Include practical tips and actionable advice
- Ensure all markdown formatting is correct
- DO NOT use literal "\\n" for line breaks — use real newlines
- Adapt content length based on the topic and user requirements
"""


        # Initialize the ReAct agent with blog generation tools
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
                - tone: Writing tone (professional, casual, adventure, luxury, budget)
                - language: Target language for the blog
                - tour_itinerary: Travel itinerary or destination information
                - creativity: Creativity level (low, medium, high)
                - user_prompt: Main topic or specific blog request
                - user_images: List of user-uploaded image URLs (optional)

        Returns:
            dict: The structured blog response with markdown content
        """
        try:
            # Extract parameters from query data
            tone = query_data.get('tone', 'casual')
            language = query_data.get('language', 'English')
            tour_itinerary = query_data.get('tour_itinerary', '')
            creativity = query_data.get('creativity', 'medium')
            user_prompt = query_data.get('user_prompt', '')
            user_images = query_data.get('user_images', [])

            # Construct the enhanced query for the agent
            enhanced_query = f"""
BLOG GENERATION REQUEST:

**Tone**: {tone}
**Language**: {language}  
**Creativity Level**: {creativity}
**Main Topic/Prompt**: {user_prompt}

**Tour Itinerary/Destination Info**: 
{tour_itinerary}

**User Uploaded Images**: {user_images if user_images else "None provided"}

INSTRUCTIONS:
1. Create a comprehensive travel blog in {language} with a {tone} tone
2. If user images are provided, analyze them using get_multimodal_capability to understand the user's travel experience
3. Use web search to gather current, accurate information about destinations mentioned
4. Use web scraping for detailed information from relevant travel websites
5. Structure the blog with proper markdown formatting
6. Include practical tips, cultural insights, and personal recommendations
7. Ensure the creativity level is {creativity} - adjust storytelling and descriptive elements accordingly
8. Make the content engaging and valuable for travelers

Create a detailed blog that travelers would find genuinely helpful and inspiring!
"""

            response = self.agent.run(enhanced_query, max_rounds=25)
            
            # Try to parse the response as JSON
            try:
                if isinstance(response, str):
                    # Look for JSON in the response
                    start_idx = response.find('{')
                    end_idx = response.rfind('}')
                    if start_idx != -1 and end_idx != -1:
                        json_str = response[start_idx:end_idx+1]
                        parsed_response = json.loads(json_str)
                        return parsed_response
                    
                # If no valid JSON found, create a fallback structure
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
                "word_count": len(agent_response.split()),
                "reading_time": f"{max(1, len(agent_response.split()) // 200)} minutes",
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
- Include relevant travel itinerary details
- Upload images if you want them analyzed

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


# Helper function to create blog generator agent instance
def create_blog_agent(model: str = "gemini-2.0-flash-exp", provider=None) -> BlogGeneratorAgent:
    """
    Create and return a BlogGeneratorAgent instance.

    Args:
        model: The LLM model to use
        provider: The LLM provider to use

    Returns:
        BlogGeneratorAgent: Configured blog generator agent
    """
    print(Fore.GREEN + "Blog Agent Model used:", Fore.YELLOW + model)
    if provider:
        print(Fore.GREEN + "Provider:", Fore.YELLOW + str(provider))
    return BlogGeneratorAgent(model=model, provider=provider)