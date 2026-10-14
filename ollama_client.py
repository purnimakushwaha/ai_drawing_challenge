
import os
from ollama import Client

# --------------------------------------------------
# OLLAMA CLOUD CONFIGURATION
# --------------------------------------------------

MODEL = "gemma4:cloud"

api_key = os.environ.get("OLLAMA_API_KEY")

if not api_key:
    raise RuntimeError(
        "OLLAMA_API_KEY is not set. Set your API key before running the app."
    )

client = Client(
    host="https://ollama.com",
    headers={"Authorization": f"Bearer {api_key}"}
)


# --------------------------------------------------
# 1. DETAILED DRAWING ANALYSIS
# --------------------------------------------------

def analyze_drawing(image_path, challenge=None, analysis_type="general"):

    if challenge:
        purpose = f"""
        This is a drawing challenge.

        Challenge instructions:
        {challenge}

        Judge how well the drawing follows the challenge.
        Do not judge only artistic perfection.
        """
    elif analysis_type == "depict":
        purpose = """
        Explain exactly what this image depicts.
        Identify visible objects, people, animals, setting,
        activities, visual details, mood and possible meaning.
        Clearly distinguish visible facts from guesses.
        """
    else:
        purpose = """
        Analyze this drawing in detail without assuming
        that it belongs to a particular challenge.
        """

    prompt = f"""
You are a friendly, thoughtful and constructive AI art expert.

{purpose}

Study the image carefully. Do not invent objects or details
that cannot reasonably be seen.

Return your analysis using these sections:

## 1. Artwork Description
Describe what is visible in the drawing in clear language.

## 2. Main Objects and Details
Identify the main objects, shapes, characters, background
and other visible details.

## 3. Creativity and Originality
Explain what is interesting or creative about the drawing.

## 4. Strengths
List 3 specific things the artist did well, where possible.

## 5. Improvement Opportunities
List up to 3 realistic improvements. Be kind and specific.

## 6. Suggestions for the Next Version
Give practical steps the artist can try next.

## 7. Overall Feedback
Give a short, encouraging summary.

"""

    if challenge:
        prompt += """
## 8. Challenge Evaluation
Score each criterion from 0 to 10:
- Relevance to the challenge
- Required elements
- Creativity
- Overall completion

Explain the scores briefly.

End with:
Score: X/10
Completed: Yes or No
Feedback: one concise sentence
"""

    response = client.chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [image_path]
            }
        ]
    )

    return response["message"]["content"]


# --------------------------------------------------
# 2. ASK AI ABOUT THE SAME DRAWING
# --------------------------------------------------

def ask_about_drawing(
    image_path,
    question,
    previous_analysis="",
    conversation_history=""
):
    prompt = f"""
You are helping a user understand and improve their drawing.

The user has already received this drawing analysis:
{previous_analysis}

Previous follow-up conversation:
{conversation_history}

The user now asks:
{question}

Answer specifically about the attached image.
Be friendly, clear, useful and detailed when necessary.

If the user asks how to improve something, give actionable
steps. If something is not clearly visible, say so instead
of pretending to know.
"""

    response = client.chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [image_path]
            }
        ]
    )

    return response["message"]["content"]


# --------------------------------------------------
# 3. COMPARE MULTIPLE DRAWINGS
# --------------------------------------------------

def compare_drawings(image_paths):

    if len(image_paths) < 2:
        raise ValueError("Upload at least two drawings to compare.")

    prompt = """
You are an objective and constructive drawing comparison expert.

The user has provided multiple drawings. Refer to them as
Drawing 1, Drawing 2, Drawing 3, and so on, in upload order.

Analyze each drawing separately, then compare them.

Include:
1. What each drawing depicts.
2. Strengths of each drawing.
3. Differences in details, composition and creativity.
4. Which drawing best communicates its idea and why.
5. One improvement suggestion for each drawing.
6. A fair overall comparison.

Do not assume that the most detailed drawing is always the best.
Explain uncertainty where image details are unclear.
Be constructive, not insulting.
"""

    response = client.chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": image_paths
            }
        ]
    )

    return response["message"]["content"]
