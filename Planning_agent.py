import json
import re

from colorama import Fore
from dotenv import load_dotenv
# from groq import Groq
import google.generativeai as genai
from tool_decorator import Tool
from tool_decorator import validate_arguments
from utils.completions import build_prompt_structure
from utils.completions import ChatHistory
from utils.completions import completions_create
from utils.completions import update_chat_history
from utils.extraction import extract_tag_content
import os

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

BASE_SYSTEM_PROMPT = ""


REACT_SYSTEM_PROMPT = """
You operate by running a loop with the following steps: Thought, Action, Observation.
You are provided with function signatures within <tools></tools> XML tags.
You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug
into functions. Pay special attention to the properties 'types'. You should use those types as in a Python dict.

CRITICAL: You MUST always use the required XML tags in your responses. Follow these patterns exactly:

PATTERN 1 - When you need to use tools:
<thought>Your reasoning about what you need to do</thought>
<tool_call>{"name": "function_name", "arguments": {"param": "value"}, "id": 0}</tool_call>

PATTERN 2 - When you have the final answer:
<response>Your complete answer to the user's question</response>

NEVER respond without using one of these patterns. The XML tags are mandatory.

For each function call return a json object with function name and arguments within <tool_call></tool_call> XML tags as follows:

<tool_call>
{"name": <function-name>,"arguments": <args-dict>, "id": <monotonically-increasing-id>}
</tool_call>

Here are the available tools / actions:

<tools>
%s
</tools>

Example session:

<question>What's the current temperature in Madrid?</question>
<thought>I need to get the current weather in Madrid</thought>
<tool_call>{"name": "get_current_weather","arguments": {"location": "Madrid", "unit": "celsius"}, "id": 0}</tool_call>

You will be called again with this:

<observation>{0: {"temperature": 25, "unit": "celsius"}}</observation>

You then output:

<response>The current temperature in Madrid is 25 degrees Celsius</response>

Additional constraints:

- If the user asks you something unrelated to any of the tools above, answer freely but ALWAYS enclose your answer with <response></response> tags.
- Always include <thought> tags when using tools to explain your reasoning
- Use incrementing IDs for multiple tool calls (0, 1, 2, etc.)
- Never respond without using the required XML tag structure
"""


class ReactAgent:
    """
    A class that represents an agent using the ReAct logic that interacts with tools to process
    user inputs, make decisions, and execute tool calls. The agent can run interactive sessions,
    collect tool signatures, and process multiple tool calls in a given round of interaction.

    Attributes:
        client (Groq): The Groq client used to handle model-based completions.
        model (str): The name of the model used for generating responses. Default is "llama-3.3-70b-versatile".
        tools (list[Tool]): A list of Tool instances available for execution.
        tools_dict (dict): A dictionary mapping tool names to their corresponding Tool instances.
    """

    def __init__(
        self,
        tools: Tool | list[Tool],
        model: str = "deepseek-r1-distill-llama-70b",
        system_prompt: str = BASE_SYSTEM_PROMPT,
    ) -> None:
        self.client = genai.GenerativeModel(model)
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools if isinstance(tools, list) else [tools]
        self.tools_dict = {tool.name: tool for tool in self.tools}

    def add_tool_signatures(self) -> str:
        """
        Collects the function signatures of all available tools.

        Returns:
            str: A concatenated string of all tool function signatures in JSON format.
        """
        return "".join([tool.fn_signature for tool in self.tools])

    def process_tool_calls(self, tool_calls_content: list) -> dict:
        """
        Processes each tool call, validates arguments, executes the tools, and collects results.

        Args:
            tool_calls_content (list): List of strings, each representing a tool call in JSON format.

        Returns:
            dict: A dictionary where the keys are tool call IDs and values are the results from the tools.
        """
        observations = {}
        malformed_calls = []
        
        for i, tool_call_str in enumerate(tool_calls_content):
            try:
                tool_call = json.loads(tool_call_str)
                
                # Validate required fields
                if "name" not in tool_call:
                    malformed_calls.append(f"Tool call {i} missing 'name' field")
                    continue
                if "arguments" not in tool_call:
                    malformed_calls.append(f"Tool call {i} missing 'arguments' field")
                    continue
                if "id" not in tool_call:
                    # Auto-assign ID if missing
                    tool_call["id"] = i
                
                tool_name = tool_call["name"]
                
                if tool_name not in self.tools_dict:
                    malformed_calls.append(f"Tool '{tool_name}' not found in available tools")
                    continue
                    
                tool = self.tools_dict[tool_name]

                print(Fore.GREEN + f"\nUsing Tool: {tool_name}")

                # Validate and execute the tool call
                validated_tool_call = validate_arguments(
                    tool_call, json.loads(tool.fn_signature)
                )
                print(Fore.GREEN + f"\nTool call dict: \n{validated_tool_call}")

                result = tool.run(**validated_tool_call["arguments"])
                print(Fore.GREEN + f"\nTool result: \n{result}")

                # Store the result using the tool call ID
                observations[validated_tool_call["id"]] = result
                
            except json.JSONDecodeError as e:
                malformed_calls.append(f"Invalid JSON in tool call {i}: {str(e)}")
                print(Fore.RED + f"Error parsing tool call JSON: {e}")
                print(Fore.RED + f"Tool call string: {tool_call_str}")
            except Exception as e:
                malformed_calls.append(f"Error processing tool call {i}: {str(e)}")
                print(Fore.RED + f"Error processing tool call: {e}")

        # Return both successful observations and any errors
        if malformed_calls:
            observations["_errors"] = malformed_calls
            
        return observations

    def run(
        self,
        user_msg: str,
        max_rounds: int = 10,
    ) -> str:
        """
        Executes a user interaction session, where the agent processes user input, generates responses,
        handles tool calls, and updates chat history until a final response is ready or the maximum
        number of rounds is reached.

        Args:
            user_msg (str): The user's input message to start the interaction.
            max_rounds (int, optional): Maximum number of interaction rounds the agent should perform. Default is 10.

        Returns:
            str: The final response generated by the agent after processing user input and any tool calls.
        """
        user_prompt = build_prompt_structure(
            prompt=user_msg, role="user", tag="question"
        )
        if self.tools:
            self.system_prompt += (
                "\n" + REACT_SYSTEM_PROMPT % self.add_tool_signatures()
            )

        chat_history = ChatHistory(
            [
                build_prompt_structure(
                    prompt=self.system_prompt,
                    role="system",
                ),
                user_prompt,
            ]
        )

        if self.tools:
            # Run the ReAct loop for max_rounds
            for round_num in range(max_rounds):
                try:
                    completion = completions_create(self.client, chat_history, self.model)
                    
                    if not completion or completion.strip() == "":
                        print(Fore.RED + f"Warning: Empty completion received in round {round_num + 1}")
                        continue

                    print(Fore.CYAN + f"\n=== Round {round_num + 1} ===")
                    print(Fore.CYAN + f"Raw completion: {completion}")

                    response = extract_tag_content(str(completion), "response")
                    if response.found and response.content:
                        return response.content[0]

                    thought = extract_tag_content(str(completion), "thought")
                    tool_calls = extract_tag_content(str(completion), "tool_call")

                    update_chat_history(chat_history, completion, "assistant")

                    # Check if the response follows the expected format
                    if not thought.found and not tool_calls.found and not response.found:
                        print(Fore.RED + f"\nLLM didn't follow the expected format in round {round_num + 1}")
                        print(Fore.RED + f"Raw response: {completion}")
                        
                        # Guide the LLM back to the correct format
                        format_correction = """Please follow the required format. You must use one of these patterns:

                            1. If you need to use tools, structure your response like this:
                            <thought>Your reasoning about what you need to do</thought>
                            <tool_call>{"name": "function_name", "arguments": {"param": "value"}, "id": 0}</tool_call>

                            2. If you have the final answer, structure it like this:
                            <response>Your final answer to the user</response>

                            Please respond again following this format."""
                        
                        update_chat_history(chat_history, format_correction, "user")
                        continue

                    # Safe access to thought content
                    if thought.found and thought.content:
                        print(Fore.MAGENTA + f"\nThought: {thought.content[0]}")
                    elif thought.found and not thought.content:
                        print(Fore.YELLOW + "\nEmpty thought tags found")

                    if tool_calls.found and tool_calls.content:
                        observations = self.process_tool_calls(tool_calls.content)
                        print(Fore.BLUE + f"\nObservations: {observations}")
                        
                        # Check if there were errors in tool calls
                        if "_errors" in observations:
                            error_msg = f"""There were errors in your tool calls:
                                {chr(10).join(observations['_errors'])}

                                Please fix these errors and provide corrected tool calls in the proper format:
                                <tool_call>{{"name": "function_name", "arguments": {{"param": "value"}}, "id": 0}}</tool_call>

                                Make sure your JSON is valid and includes all required fields (name, arguments, id)."""
                            update_chat_history(chat_history, error_msg, "user")
                            continue
                        
                        update_chat_history(chat_history, f"<observation>{observations}</observation>", "user")
                    elif tool_calls.found and not tool_calls.content:
                        print(Fore.YELLOW + "\nEmpty tool_call tags found")
                        # Guide the LLM to provide proper tool calls
                        tool_correction = """Your tool_call tags were empty. Please provide a proper tool call in this format:
                        <tool_call>{"name": "function_name", "arguments": {"param": "value"}, "id": 0}</tool_call>

                        Or if you have the final answer, use:
                        <response>Your final answer</response>"""
                        update_chat_history(chat_history, tool_correction, "user")
                        continue
                            
                except Exception as e:
                    print(Fore.RED + f"Error in round {round_num + 1}: {str(e)}")
                    print(Fore.RED + f"Completion content: {completion if 'completion' in locals() else 'N/A'}")
                    continue

        # Final fallback completion
        try:
            final_response = completions_create(self.client, chat_history, self.model)
            return final_response if final_response else "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
        except Exception as e:
            return f"I encountered an error while processing your request: {str(e)}. Please try again with a different question."