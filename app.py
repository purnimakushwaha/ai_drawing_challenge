
import os
import random
import re
import tempfile
import time

import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

from ollama_client import analyze_drawing


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="AI Drawing Studio",
    page_icon="🎨",
    layout="wide"
)


# ==================================================
# CHALLENGES
# ==================================================

CHALLENGES = {
    "🎨 Creative": [
        "Draw a dream house using at least 3 different shapes.",
        "Draw a magical tree with unusual fruits.",
        "Draw a flying vehicle from your imagination.",
        "Draw a robot with one unusual feature."
    ],
    "🔷 Geometry": [
        "Draw a house using circles and squares.",
        "Draw a robot using rectangles and circles.",
        "Draw a car using at least 3 geometric shapes.",
        "Draw a rocket using circles, rectangles and triangles."
    ],
    "😂 Funny": [
        "Draw a cat wearing a huge hat.",
        "Draw a confused-looking robot.",
        "Draw an animal trying to fly.",
        "Draw a funny face using simple shapes."
    ],
    "🎯 Challenge": [
        "Draw a tree with exactly 3 branches and 5 leaves.",
        "Draw a robot with exactly 2 circles and 3 rectangles.",
        "Draw a house with a door, two windows and a chimney.",
        "Draw a rocket with two windows and three flames."
    ]
}


# ==================================================
# SESSION STATE
# ==================================================

defaults = {
    "challenge": None,
    "result": None,
    "history": [],
    "start_time": None,
    "time_limit": 2,
    "canvas_version": 0,
    "last_analysis_mode": None,
    "last_analyzed_image": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==================================================
# HELPER: SAVE IMAGE AND ANALYZE
# ==================================================

def run_ai_analysis(image, challenge=None):
    """Save an image temporarily and send it to Ollama."""

    image_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False
        ) as temp_file:
            image_path = temp_file.name

        image.convert("RGB").save(
            image_path,
            format="PNG"
        )

        with st.spinner("🤖 AI is analyzing your drawing..."):
            result = analyze_drawing(
                image_path,
                challenge
            )

        st.session_state.result = result
        st.session_state.last_analysis_mode = (
            "challenge" if challenge else "free"
        )

        # Record scores only in Challenge Mode.
        if challenge:
            match = re.search(
                r"Score\s*:\s*(\d+)\s*/\s*10",
                result,
                re.IGNORECASE
            )

            if match:
                score = min(10, int(match.group(1)))
                st.session_state.history.append(score)

        return True

    except Exception as error:
        st.error(
            f"AI analysis failed: {error}"
        )
        return False

    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)


# ==================================================
# HEADER
# ==================================================

st.title("🎨 AI Drawing Studio")

st.write(
    "Create your own artwork, complete drawing challenges, "
    "or upload a handmade drawing for AI feedback."
)

st.caption(
    "Create. Capture. Discover."
)

st.divider()


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:
    st.header("⚙️ Settings")

    mode = st.radio(
        "Choose your experience",
        [
            "🎯 Challenge Mode",
            "🖼️ Free Drawing Mode"
        ]
    )

    st.divider()

    st.header("🏆 Challenge Score History")

    if st.session_state.history:
        for number, score in enumerate(
            st.session_state.history,
            start=1
        ):
            st.write(f"Round {number}: **{score}/10**")

        st.metric(
            "Best Score",
            f"{max(st.session_state.history)}/10"
        )

        if st.button("🗑️ Clear Score History"):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("No completed challenge rounds yet.")

    st.divider()

    st.caption(
        "AI results are generated automatically and "
        "may occasionally be inaccurate."
    )


# ==================================================
# CHALLENGE MODE
# ==================================================

if mode == "🎯 Challenge Mode":

    st.header("🎯 Drawing Challenge")

    col1, col2 = st.columns(2)

    with col1:
        category = st.selectbox(
            "Challenge category",
            list(CHALLENGES.keys())
        )

    with col2:
        time_limit = st.selectbox(
            "Time limit",
            [1, 2, 3, 5],
            index=1,
            format_func=lambda x: (
                f"{x} minute" if x == 1
                else f"{x} minutes"
            )
        )

    if st.button(
        "🎲 New Challenge",
        type="primary"
    ):
        st.session_state.challenge = random.choice(
            CHALLENGES[category]
        )
        st.session_state.result = None
        st.session_state.start_time = time.time()
        st.session_state.time_limit = time_limit
        st.session_state.canvas_version += 1
        st.rerun()

    if st.session_state.challenge is None:
        st.info(
            "Choose a category and click "
            "**New Challenge** to get started."
        )

    else:
        st.subheader("Your Mission")
        st.info(st.session_state.challenge)

        elapsed = int(
            time.time() - st.session_state.start_time
        )

        total_seconds = (
            st.session_state.time_limit * 60
        )

        remaining = max(
            0,
            total_seconds - elapsed
        )

        st.metric(
            "⏱️ Time Remaining",
            f"{remaining // 60:02d}:{remaining % 60:02d}"
        )

        if remaining == 0:
            st.warning(
                "Time is up! You can still submit your drawing."
            )

        st.subheader("✏️ Draw Your Answer")

        tool = st.selectbox(
            "Drawing tool",
            [
                "✏️ Pencil",
                "📏 Line",
                "🟦 Rectangle",
                "⭕ Circle",
                "🔺 Polygon",
                "🧹 Eraser"
            ]
        )

        drawing_modes = {
            "✏️ Pencil": "freedraw",
            "📏 Line": "line",
            "🟦 Rectangle": "rect",
            "⭕ Circle": "circle",
            "🔺 Polygon": "polygon",
            "🧹 Eraser": "freedraw"
        }

        is_eraser = tool == "🧹 Eraser"

        stroke_color = (
            "#FFFFFF"
            if is_eraser
            else st.color_picker("🎨 Drawing color", "#000000")
        )

        stroke_width = st.slider(
            "Eraser size" if is_eraser else "Brush size",
            5 if is_eraser else 1,
            50 if is_eraser else 20,
            20 if is_eraser else 4
        )

        canvas = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            background_color="#FFFFFF",
            height=450,
            width=700,
            drawing_mode=drawing_modes[tool],
            key=f"drawing_canvas_{st.session_state.canvas_version}"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ Clear Canvas"):
                st.session_state.canvas_version += 1
                st.session_state.result = None
                st.rerun()

        with col2:
            if st.button("🤖 Submit Drawing", type="primary"):
                if canvas.image_data is None:
                    st.warning("Please draw something first.")
                else:
                    image = Image.fromarray(
                        canvas.image_data.astype("uint8")
                    )

                    run_ai_analysis(
                        image,
                        st.session_state.challenge
                    )



# ==================================================
# FREE DRAWING MODE
# ==================================================

else:
    st.header("🖼️ Analyze Your Own Drawing")

    st.write(
        "Upload a handmade drawing or take a photo. "
        "No challenge is required."
    )

    source = st.radio(
        "Choose image source",
        ["📁 Upload an Image", "📷 Take a Photo"],
        horizontal=True,
        key="free_drawing_source"
    )

    uploaded_image = None

    if source == "📁 Upload an Image":

        uploaded_file = st.file_uploader(
            "Choose your drawing",
            type=["png", "jpg", "jpeg"],
            key="handmade_drawing_uploader",
            help="Select an image and click Open."
        )

        if uploaded_file is None:
            st.info(
                "Choose a PNG or JPG image from your device."
            )
        else:
            try:
                uploaded_file.seek(0)

                image = Image.open(uploaded_file)
                image.load()

                uploaded_image = image.convert("RGB")

                st.success(
                    f"Image uploaded: {uploaded_file.name}"
                )

                st.image(
                    uploaded_image,
                    caption="Your uploaded drawing",
                    use_container_width=True
                )

            except Exception as error:
                st.error(
                    f"Could not read the image: {error}"
                )

    else:
        camera_file = st.camera_input(
            "Take a picture of your drawing",
            key="handmade_drawing_camera"
        )

        if camera_file is not None:
            try:
                camera_file.seek(0)

                image = Image.open(camera_file)
                image.load()

                uploaded_image = image.convert("RGB")

                st.image(
                    uploaded_image,
                    caption="Your captured drawing",
                    use_container_width=True
                )

            except Exception as error:
                st.error(
                    f"Could not read the captured photo: {error}"
                )

    if uploaded_image is not None:

        st.divider()

        if st.button(
            "✨ Analyze My Drawing",
            type="primary",
            key="analyze_free_drawing"
        ):
            run_ai_analysis(
                uploaded_image,
                challenge=None
            )


# ==================================================
# AI RESULT
# ==================================================

if st.session_state.result:
    st.divider()
    st.header("🤖 AI Analysis Result")

    if st.session_state.last_analysis_mode == "challenge":
        st.caption("Challenge Mode · Score-based evaluation")
    else:
        st.caption("Free Drawing Mode · No challenge score")

    st.markdown(st.session_state.result)
