"""
The script reads in questions from a csv file and asks the 
specified ai model and saves the responses to an output csv file.
"""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd

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

# Input csv filename (should be in same folder as this file)
fileName = "input_questions.csv"

try:
    input_df = pd.read_csv(fileName)
except FileNotFoundError:
    print(f"Error: File '{fileName}' not found.", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error reading file '{fileName}': {e}", file=sys.stderr)
    sys.exit(1)

system_message = {
    "role": "system",
    "content": "You are a helpful assistant. Always say GO BLUE! at the end of your response.",
}

# Create a pandas DataFrame to store the outputs
output_df = pd.DataFrame(columns=["question", "response"])

# Check if 'question' column exists
if "question" not in input_df.columns:
    print(f"Error: 'question' column not found in CSV. Available columns: {list(input_df.columns)}", file=sys.stderr)
    sys.exit(1)

for index, row in input_df.iterrows():
    question = row["question"]
    
    messages = [
        system_message,
        {
            "role": "user",
            "content": question,
        }
    ]
    
    print("Asking question", str(index + 1) + ":", question)

    # Get response from AI model
    response = client.chat.completions.create(
        model=os.environ['MODEL'],
        messages=messages,
    )
    
    answer = response.choices[0].message.content
    print('question', str(index + 1) + "'s AI Response:", answer)
    
    # Add to output dataframe
    output_df.loc[len(output_df)] = [question, answer]
    print('appending question and answer', index + 1, "to output")
    print(index + 1, 'of', input_df.__len__(), "done")
    print('')

print('DONE!')

# Save output to csv file
output_df.to_csv("output.csv", index=False)