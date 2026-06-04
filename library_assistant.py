"""
Public Library Information Assistant Interface

This module provides a reusable interface for the Library Assistant chatbot
that explains library services using Google's Generative AI API.
"""

import os
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv


# System Prompt for the assistant
SYSTEM_PROMPT = """
You are a Public Library Information Assistant.

Your role:
- Explain library membership rules
- Explain book borrowing procedures
- Explain overdue policies
- Explain digital library resources

Rules:
- Do NOT issue books
- Do NOT manage user accounts
- Do NOT perform transactions
- If asked to do restricted actions, politely refuse

Respond in a clear, friendly, and simple manner.
"""


class LibraryAssistant:
    """A chatbot interface for answering library-related questions."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the LibraryAssistant.

        Args:
            api_key: Google Generative AI API key. If None, loads from .env file.
            model_name: Name of the Generative AI model to use.

        Raises:
            ValueError: If API key is not provided and not found in environment.
        """
        # Load environment variables from .env file
        load_dotenv()

        # Get API key from parameter or environment
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError(
                "API key not found. Please provide it as a parameter or set "
                "GOOGLE_API_KEY in your .env file."
            )

        # Configure the API
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def get_response(self, user_input: str) -> str:
        """
        Generate a response to a user's question about library services.

        Args:
            user_input: The user's question.

        Returns:
            The assistant's response.
        """
        if not user_input or not user_input.strip():
            return "Please enter a valid question."

        prompt = f"{SYSTEM_PROMPT}\nUser Question: {user_input}"
        response = self.model.generate_content(prompt)
        return response.text

    def chat_session(self):
        """Start an interactive chat session in the terminal."""
        print("=" * 60)
        print("📚 Public Library Information Assistant")
        print("=" * 60)
        print("\nWelcome! I can answer questions about library services.")
        print("Type 'quit' or 'exit' to end the conversation.\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ["quit", "exit"]:
                print("\nThank you for using the Library Assistant. Goodbye! 👋")
                break

            if not user_input:
                print("Please enter a question.\n")
                continue

            print("\n🤔 Thinking...")
            response = self.get_response(user_input)
            print(f"\nAssistant: {response}\n")
            print("-" * 60 + "\n")


if __name__ == "__main__":
    # Example usage
    assistant = LibraryAssistant()
    assistant.chat_session()
