from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
if not openrouter_api_key:
    raise RuntimeError(
        "OPENROUTER_API_KEY is required. Set it in the .env file."
    )

client = OpenAI(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
)

response = client.chat.completions.create(
    model="openrouter/free",
    messages=[
        {
            "role": "user",
            "content": "Hello! do you know anything about Faisalabad?"
        }
    ],
)

print(response.choices[0].message.content)


