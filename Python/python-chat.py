"""Basic example of using the Chat Completions API with the LLM Gateway.

The Chat Completions API (client.chat.completions.create) is the traditional
OpenAI-compatible endpoint. Use a 'system' role message for instructions and
a 'user' role message for the prompt. Access the reply via
response.choices[0].message.content.

For new projects, consider the Responses API (see python-responses.py), which
provides a simpler interface with built-in multi-turn and tool-use support.
"""
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

# Set the current working directory to the same directory as this file.
# This ensures the .env file is found regardless of where the script is run from.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables (API key, base URL, model name) from the .env file.
if not load_dotenv(".env"):
    print("Unable to load .env file.", file=sys.stderr)
    sys.exit(1)

# Create the OpenAI client pointed at the LLM Gateway base URL.
client = OpenAI(
    api_key=os.environ['OPENAI_API_KEY'],
    base_url=os.environ['OPENAI_API_BASE'],
)

# Maintain the running conversation history. Every turn (both the user's and
# the assistant's) is appended so the model has the full context each request.
# The 'system' message sets the assistant behavior and stays at the front.
messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant. Always say GO BLUE! at the end of your response.",
    },
]

print("Chat with the assistant. Type 'exit' or 'quit' (or Ctrl-C) to stop.\n")

while True:
    try:
        user_input = input("You: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        break

    if not user_input:
        continue
    if user_input.lower() in {"exit", "quit"}:
        break

    # Append the user's turn before sending the request.
    messages.append({"role": "user", "content": user_input})

    # Send the full conversation so the model can respond in context.
    response = client.chat.completions.create(
        model=os.environ['MODEL'],
        messages=messages,
    )

    # response.choices[0].message.content holds the assistant's reply.
    reply = response.choices[0].message.content
    print(f"\nAssistant: {reply}\n")

    # Append the assistant's turn so it's remembered on the next request.
    messages.append({"role": "assistant", "content": reply})
