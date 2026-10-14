import os
from ollama import Client

# You can override the model by setting OLLAMA_MODEL in your environment.
MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:cloud")
API_KEY = os.environ.get("OLLAMA_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "OLLAMA_API_KEY is not set. Set your API key in PowerShell before running the app."
    )

client = Client(
    host="https://ollama.com",
    headers={"Authorization": f"Bearer {API_KEY}"},
)


def _chat(prompt, images=None):
    """Send a prompt, optionally with one or more image paths, to Ollama Cloud."""
    message = {"role": "user", "content": prompt}
    if images:
        message["images"] = images

    response = client.chat(model=MODEL, messages=[message])
    return response["message"]["content"]


def generate_challenge(difficulty="Surprise me", previous_challenges=None):
    """
    Let AI choose any drawing subject/category and invent a fresh challenge.
    Recent challenges are included to reduce repetition.
    """
    previous_challenges = previous_challenges or []
    recent_text = "\n".join(
        f"- {item[:350]}" for item in previous_challenges[-8:]
    )
    if not recent_text:
        recent_text = "- None yet"

    if difficulty == "Surprise me":
        difficulty_instruction = (
            "Choose a suitable difficulty yourself. It can be easy, medium, or hard."
        )
    else:
        difficulty_instruction = f"Use this difficulty: {difficulty}."

    prompt = f"""
You are the creative challenge designer for an interactive AI Drawing Studio.

Invent ONE original drawing challenge. YOU choose the topic freely.
Do not ask the user to choose a category. You may choose anything suitable,
such as a funny invention, an unusual animal, a fantasy place, a futuristic
object, a tiny scene, a mystery, a character, nature, food, a machine, or
an unexpected combination of ideas.

Difficulty preference: {difficulty}
{difficulty_instruction}

Recent challenges to avoid repeating:
{recent_text}

Requirements:
- Make the new challenge clearly different from the recent challenges.
- Avoid generic prompts such as only "draw a cat" or "draw a house".
- Make it imaginative, specific, and enjoyable.
- Keep it possible to attempt with a mouse or touch screen.
- Use simple English a beginner can understand.
- Include one clear main subject and 3-5 visible details to include.
- Include one optional creative twist.
- Do not require writing words in the drawing.
- Do not require perfect drawing skills.
- For "Hard", add a scene or multiple connected details; for "Easy", keep
  the idea simple; for "Medium", balance simplicity and creativity.
- Keep instructions practical and not overly long.
- Do not include a solution or sample finished drawing.

Return the challenge in exactly this format:

TITLE: <short catchy title>
DIFFICULTY: <Easy, Medium, or Hard>
CHALLENGE: <clear instructions in simple English>
MUST INCLUDE: <3-5 visual details separated by commas>
BONUS TWIST: <one optional creative extra>
SUGGESTED TIME: <reasonable number of minutes>
"""
    return _chat(prompt)


def analyze_drawing(image_path, challenge=None, analysis_type="general"):
    if challenge:
        purpose = f"""
This is a drawing challenge.
Challenge instructions:
{challenge}

Evaluate how well the drawing follows this exact task. Be fair to beginners.
Do not reward only polished artistic skill. Consider relevance, required
details, creativity, and visible effort. Do not claim details are present
unless they are actually visible.
"""
    elif analysis_type == "depict":
        purpose = """
Describe what the image depicts. Identify visible objects, characters,
setting, actions, colours, composition, and mood. Clearly separate visible
facts from interpretations or guesses.
"""
    else:
        purpose = """
Give a helpful, detailed analysis of this drawing without assuming it
belongs to a challenge.
"""

    prompt = f"""
You are a kind, observant, and constructive drawing coach.
{purpose}

Use these sections:

## 1. What I Can See
Describe the drawing clearly in simple English.

## 2. Details and Composition
Mention the main objects, shapes, layout, colours, and background that are
actually visible.

## 3. What Works Well
Give up to 3 specific strengths.

## 4. What Could Be Improved
Give up to 3 constructive, achievable suggestions.

## 5. Try This Next
Give a short, practical step-by-step plan.

## 6. Creative Idea
Suggest one interesting detail the artist could add.

## 7. Overall Feedback
End with an encouraging summary.
"""
    if challenge:
        prompt += """
## 8. Challenge Evaluation
Evaluate the drawing against the challenge:
- Challenge relevance: score out of 10
- Required details: score out of 10
- Creativity: score out of 10
- Completion: score out of 10

Briefly explain each score. Calculate a fair overall score out of 10.
Do not automatically give high marks; explain the reasons kindly.
Finish with exactly these three lines:
Score: X/10
Completed: Yes or No
Feedback: one concise sentence
"""
    return _chat(prompt, images=[image_path])


def ask_about_drawing(
    image_path,
    question,
    previous_analysis="",
    conversation_history="",
):
    prompt = f"""
You are a friendly AI art coach. Answer the user's question specifically
about the attached drawing. Do not invent details that are not visible.

Earlier drawing analysis:
{previous_analysis}

Previous follow-up conversation:
{conversation_history}

User's new question:
{question}

Be clear, practical, encouraging, and specific. If asked how to improve
something, give actionable steps. If unsure about a visual detail, say so.
"""
    return _chat(prompt, images=[image_path])


def compare_drawings(image_paths):
    if len(image_paths) < 2:
        raise ValueError("Please provide at least two drawings.")

    prompt = """
Compare the attached drawings in upload order, calling them Drawing 1,
Drawing 2, and so on.

Include:
## What Each Drawing Depicts
## Strengths of Each Drawing
## Main Differences
## Composition, Details and Creativity
## Which Best Communicates Its Idea (and why)
## One Improvement for Each Drawing

Be fair and constructive. The most detailed drawing is not automatically
the best. Do not invent image details. Explain when a visual detail is unclear.
"""
    return _chat(prompt, images=image_paths)
