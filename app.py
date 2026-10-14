import os
import tempfile
from io import BytesIO

import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

from ollama_client import (
    generate_challenge,
    analyze_drawing,
    ask_about_drawing,
    compare_drawings,
)

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Drawing Studio",
    page_icon="🎨",
    layout="wide",
)

# Existing simple layout retained
st.title("🎨 AI Drawing Studio")
st.caption("Draw, explore ideas, and get thoughtful feedback from AI.")

# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
defaults = {
    "challenge_text": "",
    "challenge_title": "",
    "analysis_result": "",
    "last_drawing_bytes": None,
    "last_drawing_analysis": "",
    "drawing_questions": [],
    "last_challenge": "",
    "challenge_difficulty": "Surprise me",
    "recent_challenges": [],
    "comparison_result": "",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def image_to_png_bytes(image):
    """Convert a PIL image to PNG bytes."""
    output = BytesIO()
    image.convert("RGBA").save(output, format="PNG")
    return output.getvalue()


def save_temp_image(image_bytes):
    """Write image bytes to a temporary PNG file for Ollama."""
    temp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    try:
        temp.write(image_bytes)
        temp.close()
        return temp.name
    except Exception:
        temp.close()
        raise


def run_analysis(image_bytes, challenge=None, analysis_type="general"):
    """Analyze an image and retain it for follow-up questions."""
    image_path = None
    try:
        image_path = save_temp_image(image_bytes)

        with st.spinner("AI is carefully studying your drawing..."):
            result = analyze_drawing(
                image_path,
                challenge=challenge,
                analysis_type=analysis_type,
            )

        st.session_state["analysis_result"] = result
        st.session_state["last_drawing_bytes"] = image_bytes
        st.session_state["last_drawing_analysis"] = result
        st.session_state["last_challenge"] = challenge or ""
        st.session_state["drawing_questions"] = []
        return result
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)


def clear_current_analysis():
    """Clear the last drawing's analysis when a new challenge starts."""
    st.session_state["analysis_result"] = ""
    st.session_state["last_drawing_bytes"] = None
    st.session_state["last_drawing_analysis"] = ""
    st.session_state["last_challenge"] = ""
    st.session_state["drawing_questions"] = []


# ---------------------------------------------------------
# MAIN NAVIGATION
# ---------------------------------------------------------
mode = st.radio(
    "Choose what you want to do",
    [
        "AI Drawing Challenge",
        "Free Drawing & Analysis",
        "Compare Drawings",
    ],
    horizontal=True,
)

# ---------------------------------------------------------
# MODE 1: AI-GENERATED DRAWING CHALLENGE
# AI chooses the subject/category itself
# ---------------------------------------------------------
if mode == "AI Drawing Challenge":
    st.subheader("🎯 Your next drawing challenge")
    st.write(
        "Let AI surprise you with a fresh drawing idea from any topic — "
        "animals, fantasy, everyday life, inventions, mystery, or something unexpected."
    )

    difficulty = st.selectbox(
        "Challenge difficulty",
        ["Surprise me", "Easy", "Medium", "Hard"],
        index=0,
        key="challenge_difficulty_select",
    )

    if st.button("✨ Generate a New AI Challenge", type="primary"):
        try:
            with st.spinner("AI is inventing a new challenge..."):
                generated = generate_challenge(
                    difficulty=difficulty,
                    previous_challenges=st.session_state["recent_challenges"],
                )

            st.session_state["challenge_text"] = generated
            st.session_state["challenge_title"] = generated
            st.session_state["recent_challenges"].append(generated)
            # Keep recent history short so prompts do not grow indefinitely.
            st.session_state["recent_challenges"] = (
                st.session_state["recent_challenges"][-8:]
            )
            clear_current_analysis()
        except Exception as error:
            st.error(f"Could not generate a challenge: {error}")

    if st.session_state["challenge_text"]:
        st.info(st.session_state["challenge_text"])
        st.caption(
            "Every new challenge is created by AI. Generate another one "
            "whenever you want a different idea."
        )

        st.markdown("### ✏️ Draw your interpretation")
        canvas_col, tools_col = st.columns([3, 1])

        with tools_col:
            stroke_color = st.color_picker(
                "Brush colour", "#222222", key="challenge_color"
            )
            stroke_width = st.slider(
                "Brush size", 1, 30, 4, key="challenge_width"
            )
            bg_color = st.color_picker(
                "Canvas colour", "#FFFFFF", key="challenge_bg"
            )
            canvas_height = st.slider(
                "Canvas height", 300, 650, 450, 50, key="challenge_height"
            )

        with canvas_col:
            challenge_canvas = st_canvas(
                fill_color="rgba(255, 255, 255, 0.0)",
                stroke_width=stroke_width,
                stroke_color=stroke_color,
                background_color=bg_color,
                height=canvas_height,
                width=750,
                drawing_mode="freedraw",
                key="challenge_canvas",
                display_toolbar=True,
            )

        if st.button("🔍 Analyze My Challenge Drawing", type="primary"):
            if challenge_canvas.image_data is None:
                st.warning("Please draw something first.")
            else:
                drawing = Image.fromarray(
                    challenge_canvas.image_data.astype("uint8")
                )
                image_bytes = image_to_png_bytes(drawing)

                try:
                    result = run_analysis(
                        image_bytes,
                        challenge=st.session_state["challenge_text"],
                    )
                    st.success("Your drawing has been analyzed!")
                    st.markdown(result)
                except Exception as error:
                    st.error(f"Analysis failed: {error}")

        if (
            st.session_state["analysis_result"]
            and st.session_state["last_challenge"]
        ):
            st.markdown("### Latest challenge feedback")
            st.markdown(st.session_state["analysis_result"])

# ---------------------------------------------------------
# MODE 2: FREE DRAWING, UPLOAD AND ANALYSIS
# ---------------------------------------------------------
elif mode == "Free Drawing & Analysis":
    st.subheader("🖌️ Draw or upload an image")
    input_mode = st.radio(
        "Choose your input",
        ["Draw here", "Upload an image"],
        horizontal=True,
        key="free_input_mode",
    )

    image_bytes = None

    if input_mode == "Draw here":
        col1, col2 = st.columns([3, 1])

        with col2:
            stroke_color = st.color_picker(
                "Brush colour", "#222222", key="free_color"
            )
            stroke_width = st.slider(
                "Brush size", 1, 30, 4, key="free_width"
            )
            bg_color = st.color_picker(
                "Canvas colour", "#FFFFFF", key="free_bg"
            )
            canvas_height = st.slider(
                "Canvas height", 300, 650, 450, 50, key="free_height"
            )

        with col1:
            free_canvas = st_canvas(
                fill_color="rgba(255, 255, 255, 0.0)",
                stroke_width=stroke_width,
                stroke_color=stroke_color,
                background_color=bg_color,
                height=canvas_height,
                width=750,
                drawing_mode="freedraw",
                key="free_canvas",
                display_toolbar=True,
            )

        if free_canvas.image_data is not None:
            drawing = Image.fromarray(
                free_canvas.image_data.astype("uint8")
            )
            image_bytes = image_to_png_bytes(drawing)
            st.download_button(
                "⬇️ Download My Drawing",
                data=image_bytes,
                file_name="my_drawing.png",
                mime="image/png",
            )

    else:
        uploaded = st.file_uploader(
            "Upload a drawing or picture",
            type=["png", "jpg", "jpeg", "webp"],
            key="free_image_upload",
        )
        if uploaded is not None:
            try:
                image = Image.open(uploaded).convert("RGBA")
                st.image(
                    image,
                    caption="Image ready for analysis",
                    use_container_width=True,
                )
                image_bytes = image_to_png_bytes(image)
            except Exception as error:
                st.error(f"Could not open this image: {error}")

    if image_bytes:
        analysis_type = st.selectbox(
            "What should AI do?",
            [
                "Detailed drawing analysis",
                "Describe what this image depicts",
            ],
            key="free_analysis_type",
        )

        if st.button("✨ Analyze Image", type="primary"):
            try:
                result = run_analysis(
                    image_bytes,
                    analysis_type=(
                        "depict"
                        if analysis_type == "Describe what this image depicts"
                        else "general"
                    ),
                )
                st.success("Analysis complete!")
                st.markdown(result)
            except Exception as error:
                st.error(f"Analysis failed: {error}")

    if (
        st.session_state["analysis_result"]
        and not st.session_state["last_challenge"]
    ):
        st.markdown("### Latest AI analysis")
        st.markdown(st.session_state["analysis_result"])

# ---------------------------------------------------------
# MODE 3: COMPARE DRAWINGS
# ---------------------------------------------------------
else:
    st.subheader("🖼️ Compare two or more drawings")
    uploaded_files = st.file_uploader(
        "Select at least 2 images (up to 10)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="comparison_uploads",
    )

    if uploaded_files:
        if len(uploaded_files) > 10:
            st.warning("Please choose no more than 10 images.")
        else:
            columns = st.columns(min(len(uploaded_files), 3))
            for index, uploaded in enumerate(uploaded_files):
                with columns[index % len(columns)]:
                    st.image(
                        uploaded,
                        caption=f"Drawing {index + 1}: {uploaded.name}",
                        use_container_width=True,
                    )

            if len(uploaded_files) >= 2 and st.button(
                "🔎 Compare Drawings", type="primary"
            ):
                temp_paths = []
                try:
                    for uploaded in uploaded_files:
                        uploaded.seek(0)
                        image = Image.open(uploaded).convert("RGB")
                        temp = tempfile.NamedTemporaryFile(
                            suffix=".png", delete=False
                        )
                        temp.close()
                        image.save(temp.name, format="PNG")
                        temp_paths.append(temp.name)

                    with st.spinner("AI is comparing the drawings..."):
                        result = compare_drawings(temp_paths)

                    st.session_state["comparison_result"] = result
                    st.markdown(result)
                except Exception as error:
                    st.error(f"Comparison failed: {error}")
                finally:
                    for path in temp_paths:
                        if os.path.exists(path):
                            os.remove(path)

    if st.session_state.get("comparison_result"):
        st.markdown("### Latest comparison")
        st.markdown(st.session_state["comparison_result"])

# ---------------------------------------------------------
# FOLLOW-UP QUESTIONS ABOUT LAST ANALYZED DRAWING
# ---------------------------------------------------------
if st.session_state.get("last_drawing_bytes"):
    st.divider()
    with st.expander("💬 Ask AI About My Drawing"):
        st.write(
            "Ask a follow-up question about your latest analyzed drawing."
        )
        question = st.text_input(
            "Your question",
            placeholder="e.g. What can I add to make this drawing better?",
            key="drawing_followup_question",
        )

        if st.button("Ask AI", key="ask_drawing_ai"):
            if not question.strip():
                st.warning("Please enter a question first.")
            else:
                temp_path = None
                try:
                    temp_path = save_temp_image(
                        st.session_state["last_drawing_bytes"]
                    )
                    history = st.session_state.get("drawing_questions", [])
                    conversation_history = "\n".join(
                        f"User: {item['question']}\nAI: {item['answer']}"
                        for item in history
                    )

                    with st.spinner("AI is answering..."):
                        answer = ask_about_drawing(
                            image_path=temp_path,
                            question=question.strip(),
                            previous_analysis=st.session_state.get(
                                "last_drawing_analysis", ""
                            ),
                            conversation_history=conversation_history,
                        )

                    st.session_state["drawing_questions"].append(
                        {
                            "question": question.strip(),
                            "answer": answer,
                        }
                    )
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not get an answer: {error}")
                finally:
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)

        for item in st.session_state.get("drawing_questions", []):
            st.markdown(f"**You asked:** {item['question']}")
            st.markdown(f"**AI:** {item['answer']}")

st.caption(
    "AI feedback is a helpful estimate, not an objective measure of artistic ability."
)
