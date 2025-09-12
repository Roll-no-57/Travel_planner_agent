from crewai.flow.flow import Flow, listen, start
from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class ExampleFlow(Flow):
    model = "gemini-1.5-flash"  # you can also try "gemini-1.5-pro"

    def call_gemini(self, prompt: str) -> str:
        """Helper method to call Gemini and return text output."""
        model = genai.GenerativeModel(self.model)
        response = model.generate_content(prompt)
        return response.text.strip()

    @start()
    def generate_city(self):
        print("Starting flow")
        print(f"Flow State ID: {self.state['id']}")

        random_city = self.call_gemini("Return the name of a random city in the world.")
        self.state["city"] = random_city
        print(f"Random City: {random_city}")

        return random_city

    @listen(generate_city)
    def generate_fun_fact(self, random_city):
        fun_fact = self.call_gemini(f"Tell me a fun fact about {random_city}")
        self.state["fun_fact"] = fun_fact
        return fun_fact


flow = ExampleFlow()
flow.plot()
result = flow.kickoff()

print(f"Generated fun fact: {result}")
print(f"Generated state: {flow.state}")