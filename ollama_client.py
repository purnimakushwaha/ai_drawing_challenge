import os
from ollama import Client


api_key = os.environ.get("OLLAMA_API_KEY")

if not api_key:
    raise RuntimeError(
        "OLLAMA_API_KEY is not set. "
        "Please configure your Ollama Cloud API key."
    )


client = Client(
    host="https://ollama.com",
    headers={
        "Authorization": f"Bearer {api_key}"
    }
)


def analyze_drawing(image_path, challenge=None):

    if challenge:
        prompt = f"""
You are an AI judge for a drawing challenge.

CHALLENGE:
{challenge}

Analyze the submitted drawing carefully.

Evaluate whether the drawing follows the challenge.
Consider visible objects, shapes, details, and creativity.

Return your response in EXACTLY this format:

Score: X/10
Completed: Yes or No
Description: One short sentence describing the drawing.
Feedback: One short, helpful sentence.

Be fair. Do not claim that invisible details are present.
"""
    else:
        prompt = """
You are a friendly AI drawing analyst.

Analyze the uploaded drawing without assuming that
the user was given any challenge.

Describe only what is reasonably visible in the image.

Return your response in this format:

Title: A short title for the drawing
Description: Describe the visible drawing in 2-3 sentences.
Objects and Shapes: List the visible objects and shapes.
Colors and Style: Describe the visible colors and art style.
Strengths: Mention 2 positive aspects of the drawing.
Suggestions: Give 2 practical suggestions for improvement.
Creative Impression: Share a brief, thoughtful observation.

Do not invent details that are not visible.
Do not assign a numerical score.
Be encouraging, specific, and concise.
"""

    response = client.chat(
        model="gemma4:cloud",
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [image_path]
            }
        ]
    )

    return response["message"]["content"]
