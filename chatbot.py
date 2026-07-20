from openai import OpenAI

client = OpenAI(
    api_key="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",
    base_url="https://openrouter.ai/api/v1"
)

response = client.chat.completions.create(
    model="openrouter/free",
    messages=[
        {
            "role": "user",
            "content": "Hello!do you know anything about faisalabad"
        }
    ]
)

print(response.choices[0].message.content)


