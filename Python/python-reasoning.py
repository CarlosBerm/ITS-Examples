"""Example of using a reasoning model (e.g. o1, o3-mini) via the LLM Gateway.

Reasoning models think through problems step-by-step before responding.
They use a 'reasoning' parameter instead of temperature, and do not support:
temperature, top_p, presence_penalty, frequency_penalty, or logprobs.
Make sure your .env MODEL value is set to a reasoning-capable model.
"""
import os

from dotenv import load_dotenv
from openai import OpenAI

# Set the current working directory to the same directory as this file.
# This ensures the .env file is found regardless of where the script is run from.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables (API key, base URL, model name) from the .env file.
try:
    if load_dotenv('.env') is False:
        raise TypeError
except TypeError:
    print('Unable to load .env file.')
    quit()

# Create the OpenAI client pointed at the LLM Gateway base URL.
client = OpenAI(
    api_key=os.environ['OPENAI_API_KEY'],
    base_url=os.environ['OPENAI_API_BASE'],
)

# Send a request using the Responses API.
# reasoning.effort controls how much internal thinking the model does.
# Options: "low" (fast), "medium" (balanced), "high" (most thorough).
response = client.responses.create(
    model=os.environ['REASONING_MODEL'],
    instructions="You are a helpful assistant. Always say GO BLUE! at the end of your response.",
    input="Explain step by step. Where is the University of Michigan?",
    reasoning={"effort": "high"},
)

# Print the text content of the response.
print(response.output_text)
