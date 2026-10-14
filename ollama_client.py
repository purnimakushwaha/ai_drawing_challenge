
import os
from ollama import Client


api_key = os.environ.get("OLLAMA_API_KEY")

if not api_key:
    raise RuntimeError(
        "OLLAMA_API_KEY is not set. "
        "Configure your Ollama Cloud API key."
    )


client = Client(
    host="https://ollama.com",
    headers={
        "Authorization": f"Bearer {api_key}"
    }
)


def analyze_drawing(
    image_path,
    challenge=None,
    analysis_type="general"
):
    """Analyze one drawing or image."""

    if challenge:
        prompt = f"""
You are judging a drawing challenge.

Challenge:
{challenge}

Analyze the submitted drawing.

Return exactly this format:

Score: X/10
Completed: Yes or No
Description: Describe what is visible.
Feedback: One helpful sentence.

Judge fairly. Do not invent invisible details.
"""

    elif analysis_type == "depict":
        prompt = """
You are an AI image understanding assistant.

Explain what this image depicts.

Use this format:

Main Subject: What is the main subject?
Objects: List the visible objects and details.
Scene: Describe the scene or activity.
Visual Evidence: Explain which visible details support your answer.
Possible Meaning: Give a cautious interpretation if appropriate.

Describe only what is visible.
If something is unclear, say so instead of guessing.
Do not assign a score.
"""

    else:
        prompt = """
You are a friendly AI drawing analyst.

Analyze this drawing and return:

Title: A short title
Description: Describe the drawing in 2-3 sentences.
Objects and Shapes: List visible objects and shapes.
Colors and Style: Describe the visible colors and art style.
Strengths: Mention 2 positive aspects.
Suggestions: Give 2 practical improvement suggestions.

Be specific, supportive, and honest.
Do not invent details or assign a score.
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


def compare_drawings(image_paths):
    """Compare two or more drawing images."""

    if len(image_paths) < 2:
        raise ValueError(
            "Please provide at least two drawings to compare."
        )

    prompt = """
You are an AI visual comparison assistant.

Several images have been provided. Compare them in the
order they were uploaded: Drawing 1, Drawing 2, and so on.

Return your answer using these sections:

1. WHAT EACH DRAWING DEPICTS
Explain what is visible in each drawing separately.

2. SIMILARITIES
Identify subjects, objects, shapes, colors, or ideas
that the drawings have in common.

3. DIFFERENCES
Explain the main visible differences between the drawings.

4. DETAILS AND STYLE
Compare visible details, composition, colors, and drawing style.
Only discuss aspects that can actually be judged from the images.

5. STRENGTHS OF EACH DRAWING
Mention specific strengths of every drawing without unfairly
assuming that more detailed always means better.

6. OVERALL COMPARISON
Summarize which drawing is stronger for particular aspects,
if the images provide enough evidence. Explain why.

7. SUGGESTIONS
Give one or two useful improvement suggestions for each drawing.

Important:
- Refer to images by their upload order.
- Do not invent details.
- Do not assume the artist's age, identity, or intention.
- Be respectful and constructive.
- Do not assign numerical scores unless explicitly requested.
"""

    response = client.chat(
        model="gemma4:cloud",
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": image_paths
            }
        ]
    )

    return response["message"]["content"]
