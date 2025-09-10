import google.generativeai as genai
from typing import Optional
from groq import Groq

def completions_create(client, messages: list, model: str) -> str:
    """
    Create a completion using either Gemini or Groq depending on the client type.

    Args:
        client: google.generativeai.GenerativeModel or groq.Groq
        messages (list[dict]): Chat history
        model (str): Model name

    Returns:
        str: Assistant text output
    """
    # If using Groq, pass through chat format
    if isinstance(client, Groq):
        # Groq expects OpenAI-style messages
        response = client.chat.completions.create(messages=messages, model=model)
        # Defensive access
        try:
            return str(response.choices[0].message.content)
        except Exception:
            return ""

    # Otherwise, assume Gemini GenerativeModel
    prompt_parts = []
    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if role == 'system':
            prompt_parts.append(f"System: {content}")
        elif role == 'user':
            prompt_parts.append(f"User: {content}")
        elif role == 'assistant':
            prompt_parts.append(f"Assistant: {content}")

    full_prompt = "\n\n".join(prompt_parts)
    response = client.generate_content(full_prompt)
    return str(getattr(response, 'text', '') or '')


# def completions_create(client, messages: list, model: str) -> str:
#     """
#     Sends a request to the client's `completions.create` method to interact with the language model.

#     Args:
#         client (Groq): The Groq client object
#         messages (list[dict]): A list of message objects containing chat history for the model.
#         model (str): The model to use for generating tool calls and responses.

#     Returns:
#         str: The content of the model's response.
#     """
#     response = client.chat.completions.create(messages=messages, model=model)
#     return str(response.choices[0].message.content)


def build_prompt_structure(prompt: str, role: str, tag: str = "") -> dict:
    """
    Builds a structured prompt that includes the role and content.

    Args:
        prompt (str): The actual content of the prompt.
        role (str): The role of the speaker (e.g., user, assistant).

    Returns:
        dict: A dictionary representing the structured prompt.
    """
    if tag:
        prompt = f"<{tag}>{prompt}</{tag}>"
    return {"role": role, "content": prompt}


def update_chat_history(history: list, msg: str, role: str):
    """
    Updates the chat history by appending the latest response.

    Args:
        history (list): The list representing the current chat history.
        msg (str): The message to append.
        role (str): The role type (e.g. 'user', 'assistant', 'system')
    """
    history.append(build_prompt_structure(prompt=msg, role=role))


class ChatHistory(list):
    def __init__(self, messages: Optional[list] = None, total_length: int = -1):
        """Initialise the queue with a fixed total length.

        Args:
            messages (Optional[list]): A list of initial messages
            total_length (int): The maximum number of messages the chat history can hold.
        """
        if messages is None:
            messages = []

        super().__init__(messages)
        self.total_length = total_length

    def append(self, msg: str):
        """Add a message to the queue.

        Args:
            msg (str): The message to be added to the queue
        """
        if len(self) == self.total_length:
            self.pop(0)
        super().append(msg)


class FixedFirstChatHistory(ChatHistory):
    def __init__(self, messages: Optional[list] = None, total_length: int = -1):
        """Initialise the queue with a fixed total length.

        Args:
            messages (Optional[list]): A list of initial messages
            total_length (int): The maximum number of messages the chat history can hold.
        """
        super().__init__(messages, total_length)

    def append(self, msg: str):
        """Add a message to the queue. The first messaage will always stay fixed.

        Args:
            msg (str): The message to be added to the queue
        """
        if len(self) == self.total_length:
            self.pop(1)
        super().append(msg)