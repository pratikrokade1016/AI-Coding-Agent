import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

model = os.getenv(
    "OPENROUTER_MODEL",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
)

print("Testing model:", model)

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": "Return exactly this word: HELLO",
        }
    ],
    temperature=0,
)

print("\nRAW RESPONSE:")
print(response)

print("\nCONTENT:")
print(response.choices[0].message.content)