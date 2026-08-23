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
# PAGE
# ==================================================

st.set_page_config(
    page_title="AI Drawing Challenge",
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

if "challenge" not in st.session_state:
    st.session_state.challenge = None

if "result" not in st.session_state:
    st.session_state.result = None

if "history" not in st.session_state:
    st.session_state.history = []

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "time_limit" not in st.session_state:
    st.session_state.time_limit = 2


# ==================================================
# HEADER
# ==================================================

st.title("🎨 AI Drawing Challenge")

st.write(
    "Get a challenge, draw it directly on the canvas, "
    "and let AI judge your drawing."
)


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.header("⚙️ Challenge Settings")

    category = st.selectbox(
        "Challenge category",
        list(CHALLENGES.keys())
    )

    time_limit = st.selectbox(
        "Time limit",
        [1, 2, 3, 5],
        index=1,
        format_func=lambda x: f"{x} minute{'s' if x != 1 else ''}"
    )

    st.divider()

    st.header("🏆 Score History")

    if st.session_state.history:

        for number, score in enumerate(
            st.session_state.history,
            start=1
        ):
            st.write(
                f"Round {number}: **{score}/10**"
            )

        st.metric(
            "Best Score",
            f"{max(st.session_state.history)}/10"
        )

    else:
        st.caption("No completed rounds yet.")


# ==================================================
# NEW CHALLENGE
# ==================================================

if st.button("🎲 New Challenge", type="primary"):

    st.session_state.challenge = random.choice(
        CHALLENGES[category]
    )

    st.session_state.result = None
    st.session_state.time_limit = time_limit
    st.session_state.start_time = time.time()

    st.rerun()


# ==================================================
# CHALLENGE
# ==================================================

if st.session_state.challenge is None:

    st.info(
        "Choose a category and time limit, "
        "then click **🎲 New Challenge**."
    )

else:

    st.subheader("🎯 Your Challenge")

    st.info(st.session_state.challenge)


    # ------------------------------------------------
    # TIMER
    # ------------------------------------------------

    elapsed = int(
        time.time() - st.session_state.start_time
    )

    total_seconds = st.session_state.time_limit * 60

    remaining = max(
        0,
        total_seconds - elapsed
    )

    minutes = remaining // 60
    seconds = remaining % 60

    st.metric(
        "⏱️ Time Remaining",
        f"{minutes:02d}:{seconds:02d}"
    )

    if remaining == 0:

        st.warning(
            "⏰ Time is up! You can still submit your drawing."
        )


    # ------------------------------------------------
    # DRAWING TOOLS
    # ------------------------------------------------

    st.subheader("✏️ Draw Your Answer")

    tool = st.selectbox(
        "Choose a drawing tool",
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

    drawing_mode = drawing_modes[tool]


    # ------------------------------------------------
    # COLOR + SIZE
    # ------------------------------------------------

    if tool == "🧹 Eraser":

        stroke_color = "#FFFFFF"

        stroke_width = st.slider(
            "🧹 Eraser size",
            5,
            50,
            20
        )

    else:

        stroke_color = st.color_picker(
            "🎨 Color",
            "#000000"
        )

        stroke_width = st.slider(
            "✏️ Brush / outline size",
            1,
            20,
            4
        )


    # ------------------------------------------------
    # CANVAS
    # ------------------------------------------------

    canvas = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_color="#FFFFFF",
        height=450,
        width=700,
        drawing_mode=drawing_mode,
        key="drawing_canvas"
    )


    # ------------------------------------------------
    # CONTROLS
    # ------------------------------------------------

    col1, col2 = st.columns(2)


    with col1:

        if st.button("🗑️ Clear Canvas"):

            st.session_state.result = None

            st.rerun()


    with col2:

        if st.button("🤖 Submit Drawing"):

            if canvas.image_data is None:

                st.warning(
                    "Please draw something first."
                )

            else:

                image = Image.fromarray(
                    canvas.image_data.astype("uint8")
                )


                with tempfile.NamedTemporaryFile(
                    suffix=".png",
                    delete=False
                ) as temp_file:

                    image.save(
                        temp_file.name,
                        format="PNG"
                    )

                    image_path = temp_file.name


                try:

                    with st.spinner(
                        "🤖 AI is checking your drawing..."
                    ):

                        result = analyze_drawing(
                            image_path,
                            st.session_state.challenge
                        )

                    st.session_state.result = result


                    # --------------------------------
                    # SCORE HISTORY
                    # --------------------------------

                    match = re.search(
                        r"Score\s*:\s*(\d+)",
                        result,
                        re.IGNORECASE
                    )

                    if match:

                        score = int(
                            match.group(1)
                        )

                        st.session_state.history.append(
                            score
                        )


                except Exception as error:

                    st.error(
                        f"AI analysis failed: {error}"
                    )

                finally:

                    if os.path.exists(image_path):

                        os.remove(image_path)


    # ==================================================
    # RESULT
    # ==================================================

    if st.session_state.result:

        st.divider()

        st.subheader("🏆 AI Result")

        st.write(
            st.session_state.result
        )