
import os
import random
import re
import tempfile
import time

import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

from ollama_client import analyze_drawing, compare_drawings


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

def run_ai_analysis(
    image,
    challenge=None,
    analysis_type="general"
):
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
                challenge,
                analysis_type=analysis_type
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
# FREE DRAWING, IMAGE DESCRIPTION & COMPARISON
# ==================================================

else:
    st.header("🖼️ AI Drawing Studio")

    st.write(
        "Analyze your artwork, discover what an image depicts, "
        "or compare multiple drawings with AI."
    )

    feature = st.radio(
        "Choose a feature",
        [
            "🎨 Analyze My Drawing",
            "🔍 What Does This Image Depict?",
            "📊 Compare Drawings"
        ],
        horizontal=False,
        key="drawing_analysis_feature"
    )

    # --------------------------------------------------
    # COMPARE TWO OR MORE DRAWINGS
    # --------------------------------------------------

    if feature == "📊 Compare Drawings":

        st.subheader("📊 Compare Your Artwork")

        st.write(
            "Upload at least two images. AI will compare "
            "their subjects, similarities, differences, "
            "details, styles and strengths."
        )

        drawing_files = st.file_uploader(
            "Upload two or more drawings",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key="comparison_uploader"
        )

        if drawing_files:
            st.caption(
                f"{len(drawing_files)} image(s) selected."
            )

            if len(drawing_files) > 10:
                st.warning(
                    "Please select no more than 10 drawings."
                )

            else:
                preview_columns = st.columns(
                    min(len(drawing_files), 3)
                )

                for index, file in enumerate(drawing_files):
                    try:
                        image = Image.open(file).convert("RGB")

                        with preview_columns[
                            index % len(preview_columns)
                        ]:
                            st.image(
                                image,
                                caption=f"Drawing {index + 1}",
                                use_container_width=True
                            )

                    except Exception:
                        st.error(
                            f"Could not open {file.name}."
                        )

        if st.button(
            "🔬 Compare Drawings",
            type="primary",
            key="compare_drawings_button"
        ):
            if len(drawing_files) < 2:
                st.warning(
                    "Please upload at least two drawings."
                )

            elif len(drawing_files) > 10:
                st.warning(
                    "Please upload no more than 10 drawings."
                )

            else:
                temp_paths = []

                try:
                    for file in drawing_files:
                        file.seek(0)

                        image = Image.open(file).convert("RGB")

                        with tempfile.NamedTemporaryFile(
                            suffix=".png",
                            delete=False
                        ) as temp_file:
                            image.save(
                                temp_file.name,
                                format="PNG"
                            )
                            temp_paths.append(temp_file.name)

                    with st.spinner(
                        "🤖 AI is comparing your drawings..."
                    ):
                        result = compare_drawings(temp_paths)

                    st.session_state.result = result
                    st.session_state.last_analysis_mode = (
                        "comparison"
                    )

                except Exception as error:
                    st.error(
                        f"Drawing comparison failed: {error}"
                    )

                finally:
                    for path in temp_paths:
                        if os.path.exists(path):
                            os.remove(path)

    # --------------------------------------------------
    # ANALYZE ONE IMAGE
    # --------------------------------------------------

    else:
        if feature == "🔍 What Does This Image Depict?":
            st.subheader("🔍 Understand Any Image")

            st.write(
                "Upload or photograph a drawing to discover "
                "its main subject, visible objects, scene, "
                "and possible meaning."
            )
        else:
            st.subheader("🎨 Analyze Your Drawing")

            st.write(
                "Get a description, strengths, style observations, "
                "and suggestions for improving your artwork."
            )

        source = st.radio(
            "Choose image source",
            [
                "📁 Upload an Image",
                "📷 Take a Photo"
            ],
            horizontal=True,
            key="single_image_source"
        )

        uploaded_image = None

        if source == "📁 Upload an Image":
            uploaded_file = st.file_uploader(
                "Choose your image",
                type=["png", "jpg", "jpeg"],
                key="single_drawing_uploader"
            )

            if uploaded_file is not None:
                try:
                    uploaded_file.seek(0)
                    image = Image.open(uploaded_file)
                    image.load()
                    uploaded_image = image.convert("RGB")

                except Exception as error:
                    st.error(
                        f"Could not read the image: {error}"
                    )

        else:
            camera_file = st.camera_input(
                "Take a photo",
                key="single_drawing_camera"
            )

            if camera_file is not None:
                try:
                    camera_file.seek(0)
                    image = Image.open(camera_file)
                    image.load()
                    uploaded_image = image.convert("RGB")

                except Exception as error:
                    st.error(
                        f"Could not read the photo: {error}"
                    )

        if uploaded_image is not None:
            st.image(
                uploaded_image,
                caption="Selected image",
                use_container_width=True
            )

            if st.button(
                "✨ Analyze Image",
                type="primary",
                key="analyze_single_image_button"
            ):
                analysis_type = (
                    "depict"
                    if feature == "🔍 What Does This Image Depict?"
                    else "general"
                )

                success = run_ai_analysis(
                    uploaded_image,
                    challenge=None,
                    analysis_type=analysis_type
                )

                if success:
                    # Record which type of analysis was requested.
                    st.session_state.last_analysis_mode = (
                        "depict"
                        if analysis_type == "depict"
                        else "free"
                    )

                    # Re-run using the selected image-understanding
                    # prompt when the user chose Depict mode.
                    if analysis_type == "depict":
                        image_path = None

                        try:
                            with tempfile.NamedTemporaryFile(
                                suffix=".png",
                                delete=False
                            ) as temp_file:
                                image_path = temp_file.name

                            uploaded_image.save(
                                image_path,
                                format="PNG"
                            )

                            with st.spinner(
                                "🤖 AI is identifying the image..."
                            ):
                                result = analyze_drawing(
                                    image_path,
                                    challenge=None,
                                    analysis_type="depict"
                                )

                            st.session_state.result = result

                        except Exception as error:
                            st.error(
                                f"Image analysis failed: {error}"
                            )

                        finally:
                            if (
                                image_path
                                and os.path.exists(image_path)
                            ):
                                os.remove(image_path)


# ==================================================
# AI RESULT
# ==================================================

if st.session_state.result:
    st.divider()
    st.header("🤖 AI Analysis Result")

    result_mode = st.session_state.last_analysis_mode

    if result_mode == "challenge":
        st.caption("Challenge Mode · Score-based evaluation")
    elif result_mode == "comparison":
        st.caption("Comparison Mode · Similarities and differences")
    elif result_mode == "depict":
        st.caption("Image Understanding · What the image depicts")
    else:
        st.caption("Drawing Analysis · Feedback and suggestions")

    st.markdown(st.session_state.result)


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
