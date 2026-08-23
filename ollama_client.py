import os
from ollama import Client


api_key = os.environ.get("OLLAMA_API_KEY")

if not api_key:
    raise RuntimeError("OLLAMA_API_KEY is not set.")


client = Client(
    host="https://ollama.com",
    headers={
        "Authorization": f"Bearer {api_key}"
    }
)


def analyze_drawing(image_path, challenge):
    response = client.chat(
        model="gemma4:cloud",
        messages=[
            {
                "role": "user",
                "content": f"""
You are judging a drawing challenge.

Challenge:
{challenge}

Analyze the submitted drawing.

Return ONLY this format:

Score: X/10
Completed: Yes or No
Feedback: one short sentence

Keep the feedback concise.
""",
                "images": [image_path]
            }
        ]
    )

    return response["message"]["content"]