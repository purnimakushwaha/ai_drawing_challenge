import os
import re
import base64
import sqlite3
import tempfile
import hashlib
import hmac
import secrets
from datetime import datetime
from io import BytesIO

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

from ollama_client import (
    generate_challenge,
    analyze_drawing,
    ask_about_drawing,
    compare_drawings,
)

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="AI Drawing Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# THEME
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(ellipse at 15% 10%, rgba(92,55,160,.22), transparent 42%),
            radial-gradient(ellipse at 85% 35%, rgba(31,88,160,.17), transparent 42%),
            linear-gradient(135deg, #0b1021 0%, #11132b 55%, #101a30 100%);
        color: #f4f2ff;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #11152b; }
    h1, h2, h3, h4 { color: #f4f0ff !important; }
    p, label, li { color: #d9dcef; }
    [data-testid="stCaptionContainer"] { color: #b9c2df; }
    .hero {
        padding: 28px 26px; border-radius: 22px;
        background: linear-gradient(120deg, rgba(92,58,156,.42), rgba(29,63,115,.34));
        border: 1px solid rgba(185,164,255,.27); margin-bottom: 22px;
    }
    .hero h1 { margin: 0 0 10px 0; font-size: 2.35rem; letter-spacing: -.8px; }
    .hero p { margin-bottom: 0; line-height: 1.7; color: #e0e4ff; }
    .panel {
        padding: 22px; border-radius: 18px;
        background: rgba(28,31,64,.82);
        border: 1px solid rgba(166,146,255,.28); margin: 12px 0 20px 0;
    }
    .eyebrow { color: #c6b5ff; font-size: .78rem; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; }
    .notice {
        padding: 14px 16px; border-radius: 12px;
        background: rgba(41,54,96,.6); border: 1px solid rgba(150,169,255,.3);
        color: #e2e8ff; line-height: 1.6;
    }
    div.stButton > button[kind="primary"] {
        border: 0; border-radius: 12px; font-weight: 650; min-height: 45px;
        background: linear-gradient(100deg, #8b65e8, #5a83e9); color: white;
    }
    div.stButton > button, [data-testid="stLinkButton"] a { border-radius: 11px; }
    [data-testid="stExpander"] { border: 1px solid rgba(160,169,220,.24); border-radius: 14px; }
    [data-testid="stMetric"] {
        background: rgba(35,39,76,.65); padding: 14px; border-radius: 13px;
        border: 1px solid rgba(160,169,220,.18);
    }
    /* Clear, consistent controls */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-testid="stNumberInput"] input {
        border-radius: 10px !important;
    }
    [data-testid="stFileUploader"] section {
        border: 1px dashed rgba(180,170,255,.55);
        border-radius: 14px;
        background: rgba(28,31,64,.42);
    }
    div.stButton > button {
        min-height: 42px;
        white-space: normal;
        transition: transform .15s ease, border-color .15s ease;
    }
    div.stButton > button:hover { border-color: #b8a2ff; transform: translateY(-1px); }
    [data-testid="stRadio"] > div { gap: 8px; }
    [data-testid="stRadio"] label {
        background: rgba(40,43,82,.68);
        border: 1px solid rgba(166,146,255,.22);
        border-radius: 12px;
        padding: 9px 12px;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button { text-align: left; }
    [data-testid="stExpander"] summary { font-weight: 650; }
    .quick-start {
        display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px; margin: 8px 0 22px;
    }
    .quick-step {
        padding: 15px; border-radius: 14px;
        background: rgba(28,31,64,.68);
        border: 1px solid rgba(166,146,255,.22);
    }
    .quick-step strong { display:block; margin-bottom:5px; color:#f4f0ff; }
    .quick-step span { color:#cbd2ed; font-size:.92rem; line-height:1.45; }
    .section-hint { color:#cbd2ed; margin-top:-5px; margin-bottom:14px; }
    @media (max-width: 700px) {
        .hero { padding: 20px 16px; }
        .hero h1 { font-size: 1.8rem; }
        .panel { padding: 16px; }
        .quick-start { grid-template-columns: 1fr; gap: 8px; }
        .quick-step { padding: 12px; }
    }

    /* Premium creative-workspace styling inspired by the references */
    .stApp {
        background:
          radial-gradient(ellipse at 7% 2%, rgba(114,61,255,.24), transparent 34%),
          radial-gradient(ellipse at 94% 18%, rgba(22,139,255,.18), transparent 32%),
          radial-gradient(ellipse at 52% 100%, rgba(209,52,159,.12), transparent 38%),
          #080b17;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #151725 0%, #10121f 100%);
        border-right: 1px solid rgba(139,150,210,.17);
    }
    [data-testid="stSidebar"] > div { padding-top: 1.25rem; }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        letter-spacing: -.3px;
    }
    .hero {
        position: relative; overflow: hidden;
        background:
          radial-gradient(circle at 85% 5%, rgba(87,121,255,.27), transparent 32%),
          linear-gradient(115deg, rgba(90,44,160,.34), rgba(18,43,85,.58) 60%, rgba(22,24,48,.88));
        border: 1px solid rgba(144,137,255,.34);
        box-shadow: 0 18px 55px rgba(0,0,0,.22), inset 0 1px rgba(255,255,255,.05);
        padding: 30px 30px 28px;
    }
    .hero:after {
        content: "✦"; position: absolute; right: 5%; top: 10%;
        color: rgba(208,196,255,.65); font-size: 3.4rem;
        text-shadow: 0 0 24px rgba(147,105,255,.65);
    }
    .hero h1 {
        background: linear-gradient(90deg,#f7d8ff,#b6caff 60%,#8be4ff);
        -webkit-background-clip: text; background-clip: text; color: transparent !important;
        font-size: clamp(2rem, 4vw, 3rem); line-height: 1.08;
    }
    .eyebrow { color:#b9a7ff; letter-spacing:2px; }
    .quick-step, .panel {
        background: linear-gradient(145deg, rgba(25,30,57,.94), rgba(16,20,39,.94));
        border: 1px solid rgba(139,151,219,.22);
        box-shadow: 0 8px 26px rgba(0,0,0,.13), inset 0 1px rgba(255,255,255,.025);
        transition: border-color .2s ease, transform .2s ease;
    }
    .quick-step:hover, .panel:hover { border-color:rgba(153,126,255,.48); }
    .quick-step strong { color:#f3edff; }
    .quick-step span { color:#bfc8e6; }
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        background: rgba(17,21,42,.9); border:1px solid rgba(144,153,216,.18);
        padding:5px; border-radius:14px; gap:5px;
    }
    [data-testid="stTabs"] button[role="tab"] {
        border-radius:10px; padding:10px 16px; transition:all .2s ease;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background:linear-gradient(110deg,#7954dc,#426ee0); color:white;
    }
    div.stButton > button[kind="primary"], button[kind="primaryFormSubmit"] {
        background:linear-gradient(100deg,#8b5cf6,#4f7cf3);
        box-shadow:0 5px 18px rgba(91,91,230,.22);
        border:1px solid rgba(255,255,255,.12);
    }
    div.stButton > button:not([kind="primary"]) {
        background:rgba(35,40,69,.85); border:1px solid rgba(144,153,216,.2);
        color:#e7eaff;
    }
    div.stButton > button:hover {
        border-color:#a994ff; box-shadow:0 7px 20px rgba(70,70,170,.16);
    }
    [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input {
        background:rgba(17,22,43,.92); border-color:rgba(143,153,217,.3);
    }
    [data-testid="stFileUploader"] section {
        background:linear-gradient(135deg,rgba(29,33,63,.8),rgba(17,21,40,.8));
        border:1px dashed rgba(151,133,255,.55);
    }
    [data-testid="stMetric"] {
        background:linear-gradient(145deg,rgba(35,41,78,.78),rgba(20,25,49,.78));
        border:1px solid rgba(142,153,222,.2);
        box-shadow:inset 0 1px rgba(255,255,255,.03);
    }
    [data-testid="stExpander"], [data-testid="stAlert"] {
        border-radius:14px; border-color:rgba(144,153,216,.22);
    }
    [data-testid="stImage"] img { border-radius:12px; }
    hr { border-color:rgba(142,153,222,.18); }

    .gallery-card {
        background: linear-gradient(145deg, rgba(25,30,57,.96), rgba(13,17,34,.96));
        border: 1px solid rgba(139,151,219,.24); border-radius: 16px;
        padding: 10px 10px 14px; margin-bottom: 16px;
        box-shadow: 0 10px 28px rgba(0,0,0,.16);
    }
    .gallery-card [data-testid="stImage"] img { aspect-ratio: 4 / 3; object-fit: cover; }
    .gallery-tag {
        display: inline-block; margin: 3px 0 8px; padding: 4px 8px;
        border-radius: 999px; color: #d9ceff; font-size: .76rem;
        background: rgba(126,91,224,.18); border: 1px solid rgba(160,130,255,.25);
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(151,134,255,.25) !important;
        border-radius: 16px !important;
        background: linear-gradient(145deg, rgba(25,30,57,.70), rgba(13,17,34,.68));
    }
    @media (max-width: 700px) {
        .hero { padding:22px 18px; }
        .hero:after { right:4%; top:4%; font-size:2rem; }
        .hero h1 { max-width:85%; font-size:1.8rem; }
        [data-testid="stTabs"] button[role="tab"] { padding:8px 9px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# SESSION STATE
# =========================================================
DEFAULTS = {
    "challenge_text": "",
    "recent_challenges": [],
    "analysis_result": "",
    "analysis_context": "",
    "last_drawing_bytes": None,
    "last_drawing_analysis": "",
    "last_challenge": "",
    "drawing_questions": [],
    "comparison_result": "",
    "history_selected_id": None,
    "current_user": None,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================================================
# IMAGE HELPERS
# =========================================================
def image_to_png_bytes(image):
    output = BytesIO()
    image.convert("RGBA").save(output, format="PNG")
    return output.getvalue()


def save_temp_image(image_bytes):
    temp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    try:
        temp.write(image_bytes)
        temp.close()
        return temp.name
    except Exception:
        temp.close()
        raise


def run_analysis(image_bytes, challenge=None, analysis_type="general", context="upload"):
    image_path = None
    try:
        image_path = save_temp_image(image_bytes)
        with st.spinner("✨ Your AI art coach is studying the drawing..."):
            result = analyze_drawing(
                image_path,
                challenge=challenge,
                analysis_type=analysis_type,
            )
        st.session_state["analysis_result"] = result
        st.session_state["analysis_context"] = context
        st.session_state["last_drawing_bytes"] = image_bytes
        st.session_state["last_drawing_analysis"] = result
        st.session_state["last_challenge"] = challenge or ""
        st.session_state["drawing_questions"] = []
        return result
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)


def clear_analysis():
    st.session_state["analysis_result"] = ""
    st.session_state["analysis_context"] = ""
    st.session_state["last_drawing_bytes"] = None
    st.session_state["last_drawing_analysis"] = ""
    st.session_state["last_challenge"] = ""
    st.session_state["drawing_questions"] = []

# =========================================================
# SQLITE DRAWING HISTORY
# =========================================================
HISTORY_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drawing_history.db")


def init_history_db():
    with sqlite3.connect(HISTORY_DB) as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        connection.execute(
            """CREATE TABLE IF NOT EXISTS drawing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                mode TEXT NOT NULL,
                challenge TEXT NOT NULL DEFAULT '',
                image BLOB NOT NULL,
                analysis TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )"""
        )
        columns = {row[1] for row in connection.execute("PRAGMA table_info(drawing_history)")}
        if "user_id" not in columns:
            connection.execute("ALTER TABLE drawing_history ADD COLUMN user_id INTEGER")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_history_user_id ON drawing_history(user_id, id DESC)")
        connection.commit()


def _password_digest(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 260_000).hex()


def create_account(username, password):
    username = username.strip()
    if len(username) < 3:
        return False, "Username must contain at least 3 characters."
    if len(username) > 32 or not re.fullmatch(r"[A-Za-z0-9_.-]+", username):
        return False, "Use 3–32 characters: letters, numbers, dot, underscore or hyphen."
    if len(password) < 8:
        return False, "Password must contain at least 8 characters."
    salt = secrets.token_hex(16)
    digest = _password_digest(password, salt)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with sqlite3.connect(HISTORY_DB) as connection:
            cursor = connection.execute(
                "INSERT INTO users (username, password_hash, salt, created_at) VALUES (?, ?, ?, ?)",
                (username, digest, salt, now),
            )
            connection.commit()
            return True, cursor.lastrowid
    except sqlite3.IntegrityError:
        return False, "That username is already taken. Please choose another."


def authenticate_user(username, password):
    with sqlite3.connect(HISTORY_DB) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT id, username, password_hash, salt FROM users WHERE username = ? COLLATE NOCASE",
            (username.strip(),),
        ).fetchone()
    if not row:
        return None
    candidate = _password_digest(password, row["salt"])
    if hmac.compare_digest(candidate, row["password_hash"]):
        return {"id": row["id"], "username": row["username"]}
    return None


def render_auth_screen():
    st.markdown("""<div class="hero"><h1> (◖⁠⚆‿⚆⁠◗)𝐀𝐈 𝐃𝐫𝐚𝐰𝐢𝐧𝐠 𝐒𝐭𝐮𝐝𝐢𝐨｡°・*｡˙⁠✿｡☆ﾟ⁠.✿*⁠･⁠｡ﾟ</h1><p>A friendly space to sketch, try creative challenges, and get helpful feedback from your AI art coach.)</p></div>""", unsafe_allow_html=True)
    st.markdown("""
    <div class="quick-start">
      <div class="quick-step"><strong>🎯 Get an idea</strong><span>Generate a drawing challenge or start with a blank canvas.</span></div>
      <div class="quick-step"><strong>✏️ Make it yours</strong><span>Draw at your own pace. There is no perfect or wrong drawing.</span></div>
      <div class="quick-step"><strong>💡 Learn and revisit</strong><span>Ask AI for suggestions and save your artwork in your account.</span></div>
    </div>
    """, unsafe_allow_html=True)
    login_tab, signup_tab = st.tabs(["🔐 Log in", "✨ Create an account"])
    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
        if submitted:
            user = authenticate_user(username, password)
            if user:
                st.session_state["current_user"] = user
                st.rerun()
            else:
                st.error("Username or password is incorrect.")
    with signup_tab:
        st.caption("Choose a username with 3–32 letters, numbers, dots, underscores or hyphens. Use a password with at least 8 characters.")
        st.caption("Your password is stored as a salted hash, not as plain text.")
        with st.form("signup_form"):
            new_username = st.text_input("Create username", key="signup_username")
            new_password = st.text_input("Create password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm password", type="password", key="signup_confirm_password")
            submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
        if submitted:
            if new_password != confirm_password:
                st.error("The passwords do not match.")
            else:
                ok, result = create_account(new_username, new_password)
                if ok:
                    st.session_state["current_user"] = {"id": result, "username": new_username.strip()}
                    st.success("Account created. You're now logged in!")
                    st.rerun()
                else:
                    st.error(result)


def save_history(user_id, title, mode, challenge, image_bytes, analysis=""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(HISTORY_DB) as connection:
        cursor = connection.execute(
            """INSERT INTO drawing_history
               (user_id, title, mode, challenge, image, analysis, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, title, mode, challenge or "", sqlite3.Binary(image_bytes), analysis or "", now, now),
        )
        connection.commit()
        return cursor.lastrowid


def get_history(user_id, limit=30):
    with sqlite3.connect(HISTORY_DB) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """SELECT id, title, mode, challenge, analysis, created_at, updated_at
               FROM drawing_history WHERE user_id = ? ORDER BY id DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]


def get_history_item(record_id, user_id):
    with sqlite3.connect(HISTORY_DB) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM drawing_history WHERE id = ? AND user_id = ?", (record_id, user_id)
        ).fetchone()
        return dict(row) if row else None


# Initialise accounts/history before showing the login screen.
init_history_db()
if not st.session_state.get("current_user"):
    render_auth_screen()
    st.stop()
CURRENT_USER = st.session_state["current_user"]

# Lightweight in-page drawing canvas. The browser only sends the drawing to
# Python when the user clicks Save Drawing or Analyze Drawing.
drawing_canvas_component = components.declare_component(
    "ai_drawing_studio_canvas",
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "drawing_canvas"),
)


def challenge_sections(challenge):
    """Extract must-include items, bonus twist and time from generated challenge text."""
    text = (challenge or "").strip()
    must_match = re.search(
        r"MUST\s+INCLUDE\s*:\s*(.*?)(?=BONUS\s+TWIST\s*:|SUGGESTED\s+TIME\s*:|DIFFICULTY\s*:|$)",
        text, flags=re.IGNORECASE | re.DOTALL,
    )
    bonus_match = re.search(
        r"BONUS\s+TWIST\s*:\s*(.*?)(?=SUGGESTED\s+TIME\s*:|DIFFICULTY\s*:|$)",
        text, flags=re.IGNORECASE | re.DOTALL,
    )
    time_match = re.search(r"SUGGESTED\s+TIME\s*:\s*([^\n]+)", text, flags=re.IGNORECASE)

    def split_items(value):
        if not value:
            return []
        cleaned = re.sub(r"[\r\n]+", " ", value)
        cleaned = re.sub(r"\s*[•·]\s*", ", ", cleaned)
        parts = [re.sub(r"^[\s\-*]+|[\s.;]+$", "", part) for part in cleaned.split(",")]
        return [part for part in parts if part]

    return {
        "must_include": split_items(must_match.group(1) if must_match else ""),
        "bonus": (bonus_match.group(1).strip(" \n\r.;") if bonus_match else ""),
        "time": (time_match.group(1).strip() if time_match else ""),
    }


def render_robot_reference():
    """A simple schematic reference, not an image to submit as the user's drawing."""
    st.markdown(
        """
        <div class="panel">
          <div class="eyebrow">QUICK VISUAL REFERENCE · INSPIRATION ONLY</div>
          <svg viewBox="0 0 660 310" role="img" aria-label="Simple recycled robot chef sketch guide" style="width:100%;max-width:660px;display:block;margin:8px auto 0;background:#fff;border-radius:14px">
            <g stroke="#24233d" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" fill="none">
              <!-- colander hat -->
              <path d="M245 67 Q330 18 415 67 L402 88 L258 88 Z" fill="#d7e2ed"/>
              <path d="M263 59 L397 59 M279 43 L286 75 M310 34 L313 79 M342 34 L342 79 M373 43 L367 75" stroke-width="2.5"/>
              <!-- fork arms -->
              <path d="M248 143 L194 168 L157 148"/>
              <path d="M157 148 L145 120 M157 148 L166 117 M157 148 L180 128" stroke-width="3.5"/>
              <path d="M412 143 L466 168 L505 148"/>
              <path d="M505 148 L518 120 M505 148 L496 117 M505 148 L482 128" stroke-width="3.5"/>
              <!-- toaster body -->
              <rect x="248" y="86" width="164" height="139" rx="22" fill="#ffca75"/>
              <path d="M277 108 L383 108" stroke-width="3"/>
              <rect x="279" y="124" width="102" height="45" rx="10" fill="#f5f6fa" stroke-width="3"/>
              <circle cx="304" cy="145" r="5" fill="#24233d" stroke-width="2"/><circle cx="356" cy="145" r="5" fill="#24233d" stroke-width="2"/>
              <path d="M310 158 Q330 174 350 158"/>
              <circle cx="393" cy="190" r="6" fill="#e75b68" stroke-width="2"/>
              <path d="M289 225 L278 247 M371 225 L382 247"/>
              <!-- tiny pan -->
              <path d="M410 195 L461 195"/><ellipse cx="426" cy="184" rx="22" ry="8" fill="#d6d9e2"/><path d="M447 184 L475 177"/>
              <!-- soda can pet -->
              <path d="M95 210 L105 186 L151 186 L161 210 L157 263 Q128 276 99 263 Z" fill="#7fd6cf"/>
              <ellipse cx="128" cy="188" rx="23" ry="6" fill="#c7f0ec"/>
              <path d="M118 187 Q128 180 138 187" stroke-width="2.5"/>
              <circle cx="117" cy="224" r="3.5" fill="#24233d" stroke-width="2"/><circle cx="139" cy="224" r="3.5" fill="#24233d" stroke-width="2"/>
              <path d="M119 238 Q128 246 137 238" stroke-width="3"/>
              <path d="M104 250 L91 258 M156 250 L169 258" stroke-width="3"/>
              <!-- plate/food -->
              <ellipse cx="330" cy="270" rx="88" ry="17" fill="#f2f4fa"/>
              <path d="M298 262 Q285 245 302 239 Q315 230 325 248 Q342 229 354 243 Q372 257 354 264 Z" fill="#76bd8c" stroke-width="3"/>
              <path d="M309 250 L320 257 M341 246 L337 257" stroke-width="2.5"/>
            </g>
            <g fill="#3b3a56" font-family="Arial,sans-serif" font-size="15" font-weight="700">
              <text x="25" y="290">Soda-can pet</text><text x="450" y="36">Colander hat</text><text x="452" y="103">Fork arms</text><text x="433" y="236">Tiny pan</text><text x="270" y="300">Toaster body + meal</text>
            </g>
            <g stroke="#777b9a" stroke-width="1.5" fill="none" stroke-dasharray="4 4"><path d="M112 274 L102 282"/><path d="M450 42 L408 57"/><path d="M452 108 L429 139"/><path d="M440 229 L445 192"/></g>
          </svg>
          <p style="color:#cfd6f3;font-size:13px;margin:10px 2px 0">Use this as a rough idea only. Your own version can look completely different.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_challenge_guide(challenge):
    sections = challenge_sections(challenge)
    lower = (challenge or "").lower()
    st.markdown("### 🧩 Make the challenge easier")
    st.caption("Tick each item when you've added it to your own drawing.")

    if sections["must_include"]:
        with st.container(border=True):
            st.markdown("**Required items**")
            for index, item in enumerate(sections["must_include"]):
                st.checkbox(item, key=f"challenge_check_{st.session_state.get('challenge_version', 0)}_{index}")
    if sections["bonus"]:
        with st.container(border=True):
            st.markdown("**⭐ Bonus twist**")
            st.checkbox(sections["bonus"], key=f"challenge_bonus_{st.session_state.get('challenge_version', 0)}")
    if sections["time"]:
        st.caption(f"⏱️ Suggested time: {sections['time']}")

    if "toaster" in lower and "robot" in lower:
        render_robot_reference()
        st.markdown("**Suggested drawing order**")
        steps = [
            "Draw a large rounded rectangle for the toaster body.",
            "Add a face and a colander-shaped hat on top.",
            "Draw two mismatched fork arms on the sides.",
            "Add a tiny frying pan and a fancy meal (steam, vegetables or a garnish).",
            "Draw a little soda-can pet beside the robot.",
            "Finish with colours, recycled-material details and a background.",
        ]
        for number, step in enumerate(steps, start=1):
            st.markdown(f"**{number}.** {step}")
    elif sections["must_include"]:
        st.info("Tip: start with the biggest shape, add the required items, then finish with colour and small details.")


def render_creative_canvas(show_challenge=True, canvas_id="free"):
    is_challenge_canvas = canvas_id == "challenge"
    """Show the built-in drawing canvas and handle save/analyze actions."""
    challenge = st.session_state.get("challenge_text", "").strip()
    if challenge and show_challenge:
        st.markdown("### 🎯 Your drawing challenge")
        st.info(challenge)
        render_challenge_guide(challenge)

    st.subheader("🎯 Challenge Canvas" if is_challenge_canvas else "🪄 Draw Your Own Canvas")
    st.write(
        "Draw your interpretation of the challenge below." if is_challenge_canvas else
        "Start with a blank canvas. This drawing stays separate from your challenge artwork."
    )
    st.markdown(
        """
        <div class="notice">
        <b>Quick guide:</b> Use the canvas tools to sketch. Choose <b>Save Drawing</b> to keep a copy in your gallery, or
        <b>Analyze Drawing</b> to ask the AI art coach for constructive feedback. You can save first and analyze later, too.
        </div>
        """,
        unsafe_allow_html=True,
    )

    canvas_result = drawing_canvas_component(
        key=f"drawing_canvas_{canvas_id}",
        reset_token=st.session_state.get(f"canvas_reset_token_{canvas_id}", 0),
        default_height=560,
        default_width=1000,
        component_height=650,
    )

    canvas_action_timestamp = (
        canvas_result.get("timestamp") if isinstance(canvas_result, dict) else None
    )
    processed_key = f"canvas_last_processed_timestamp_{canvas_id}"
    if (
        isinstance(canvas_result, dict)
        and canvas_result.get("action") in {"save", "analyze"}
        and canvas_action_timestamp != st.session_state.get(processed_key)
    ):
        st.session_state[processed_key] = canvas_action_timestamp
        data_url = canvas_result.get("png_data_url", "")
        if not data_url.startswith("data:image/png;base64,"):
            st.error("The canvas did not return a valid PNG. Please draw again and retry.")
            return

        try:
            image_bytes = base64.b64decode(data_url.split(",", 1)[1])
            if not image_bytes:
                st.warning("The canvas is empty. Draw something first.")
            elif canvas_result.get("action") == "save":
                record_id = save_history(
                    user_id=CURRENT_USER["id"],
                    title=(challenge if is_challenge_canvas and challenge else "My Creative Drawing"),
                    mode=("AI Drawing Challenge" if is_challenge_canvas else "Creative Canvas"),
                    challenge=(challenge if is_challenge_canvas else ""),
                    image_bytes=image_bytes,
                    analysis="",
                )
                st.session_state["latest_history_id"] = record_id
                st.session_state["last_drawing_bytes"] = image_bytes
                st.success("Drawing saved to Drawing History. You can also download it using the PNG button on the canvas.")
                st.image(image_bytes, caption="Saved drawing", use_container_width=True)
            else:
                result = run_analysis(
                    image_bytes,
                    challenge=(challenge or None) if is_challenge_canvas else None,
                    analysis_type="general",
                    context=("challenge" if is_challenge_canvas else "free"),
                )
                record_id = save_history(
                    user_id=CURRENT_USER["id"],
                    title=(challenge if is_challenge_canvas and challenge else "My Creative Drawing"),
                    mode=("AI Drawing Challenge" if is_challenge_canvas else "Creative Canvas"),
                    challenge=(challenge if is_challenge_canvas else ""),
                    image_bytes=image_bytes,
                    analysis=result,
                )
                st.session_state["latest_history_id"] = record_id
                st.success("AI analysis complete! Your drawing and feedback were saved in Drawing History.")
        except Exception as error:
            st.error(f"Could not process the drawing: {error}")

# =========================================================
# SIDEBAR: HISTORY
# =========================================================
with st.sidebar:
    st.markdown(
        "<div style='padding:12px 13px;margin-bottom:16px;border-radius:14px;"
        "background:linear-gradient(120deg,rgba(111,75,220,.25),rgba(44,94,178,.15));"
        "border:1px solid rgba(151,134,255,.25)'>"
        "<div style='font-size:11px;letter-spacing:1.8px;color:#b8a7ff;font-weight:800'>✦ CREATIVE WORKSPACE</div>"
        "<div style='font-size:19px;font-weight:800;margin-top:4px;color:#f4f0ff'>AI Drawing Studio</div>"
        "<div style='font-size:12px;color:#bfc8e6;margin-top:3px'>Your ideas, your gallery</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"## 👋 {CURRENT_USER['username']}")
    if st.button("Log out", use_container_width=True):
        st.session_state["current_user"] = None
        st.session_state["history_selected_id"] = None
        st.rerun()
    st.divider()
    st.markdown("## 🗂️ My Drawing History")
    st.caption("Only your own saved drawings appear here. Select a drawing to preview its image and AI feedback.")
    saved_items = get_history(CURRENT_USER["id"])
    if not saved_items:
        st.info("Nothing saved yet. Use Save Drawing or Analyze Drawing on a canvas to start your personal gallery.")
    else:
        for item in saved_items:
            if st.button(
                f"🎨 {item['title'][:27]}",
                key=f"history_{item['id']}",
                use_container_width=True,
                help=f"{item['mode']} · {item['created_at']}",
            ):
                st.session_state["history_selected_id"] = item["id"]
                st.rerun()

# =========================================================
# HEADER AND NAVIGATION
# =========================================================
st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">YOUR PERSONAL CREATIVE SPACE</div>
        <h1>🌌 AI Drawing Studio</h1>
        <p>Turn ideas into drawings, experiment without pressure, and use AI feedback to discover what to try next. Your saved gallery is available from the sidebar.</p>
    </div>
    <div class="quick-start">
      <div class="quick-step"><strong>1 · Choose a mode</strong><span>Pick a challenge, blank canvas, upload, or comparison.</span></div>
      <div class="quick-step"><strong>2 · Create or add art</strong><span>Follow the on-screen instructions and use the canvas tools.</span></div>
      <div class="quick-step"><strong>3 · Save or get feedback</strong><span>Save your work, then review the result below the canvas.</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='eyebrow'>WORKSPACE NAVIGATION</div>", unsafe_allow_html=True)
mode = st.selectbox(
    "What would you like to do today?",
    [
        "🎯 AI Drawing Challenge",
        "🪄 Creative Canvas",
        "🖼️ Upload & AI Analysis",
        "🗂️ My Gallery",
        "🖼️ Compare Drawings",
    ],
    key="main_navigation",
    help="Choose one activity. Your challenge drawing and blank-canvas drawing use separate canvases.",
)

# =========================================================
# MODE 1: AI DRAWING CHALLENGE
# =========================================================
if mode == "🎯 AI Drawing Challenge":
    st.subheader("✨ Discover your next creative quest")
    st.write("Get a creative prompt, follow the checklist if you like, and draw in the challenge's own canvas.")

    difficulty = st.selectbox(
        "Choose your challenge level",
        ["Surprise me", "Easy", "Medium", "Hard"],
        key="challenge_difficulty",
        help="Easy = simpler idea; Medium = a few extra details; Hard = a more imaginative challenge. Surprise me lets AI choose.",
    )
    difficulty_notes = {
        "Surprise me": "Not sure what to draw? Let AI pick a level for you.",
        "Easy": "A relaxed warm-up with a simple idea.",
        "Medium": "A little more detail and imagination.",
        "Hard": "A bigger creative puzzle—take it one step at a time.",
    }
    st.caption(difficulty_notes[difficulty])

    if st.button("✨ Generate a New Challenge", type="primary", use_container_width=True):
        try:
            with st.spinner("🌠 Dreaming up your next drawing quest..."):
                generated = generate_challenge(
                    difficulty=difficulty,
                    previous_challenges=st.session_state["recent_challenges"],
                )
            st.session_state["challenge_text"] = generated
            st.session_state["canvas_reset_token_challenge"] = st.session_state.get("canvas_reset_token_challenge", 0) + 1
            st.session_state["challenge_version"] = st.session_state.get("challenge_version", 0) + 1
            st.session_state["recent_challenges"].append(generated)
            st.session_state["recent_challenges"] = st.session_state["recent_challenges"][-8:]
            clear_analysis()
        except Exception as error:
            st.error(f"Could not generate a challenge: {error}")

    if st.session_state.get("challenge_text"):
        st.markdown(
            "<div class='panel'><div class='eyebrow'>YOUR NEW AI QUEST</div><p>Your dedicated challenge canvas is ready below. Draw your idea, then analyze it without leaving this page.</p></div>",
            unsafe_allow_html=True,
        )
        render_creative_canvas(show_challenge=True, canvas_id="challenge")
        if st.session_state.get("analysis_result") and st.session_state.get("analysis_context") == "challenge":
            st.divider()
            with st.container(border=True):
                st.markdown("<div class='eyebrow'>YOUR AI ART COACH</div>", unsafe_allow_html=True)
                st.subheader("🏆 Your Challenge Feedback")
                st.markdown(st.session_state["analysis_result"])
    else:
        st.info("Your next quest is waiting. Generate a challenge to begin!")

# =========================================================
# MODE 2: LIGHTWEIGHT BUILT-IN CREATIVE CANVAS
# =========================================================
elif mode == "🪄 Creative Canvas":
    st.subheader("🪄 Draw Your Own")
    st.write("Want to draw whatever you like? Start fresh here. This blank canvas is separate from your challenge artwork.")
    render_creative_canvas(show_challenge=False, canvas_id="free")

    if st.session_state.get("analysis_result") and st.session_state.get("analysis_context") == "free":
        st.divider()
        with st.container(border=True):
            st.markdown("<div class='eyebrow'>YOUR AI ART COACH</div>", unsafe_allow_html=True)
            st.subheader("💡 Your AI Feedback")
            st.markdown(st.session_state["analysis_result"])

# =========================================================
# MODE 3: UPLOAD IMAGE & AI ANALYSIS (PRESERVED WORKFLOW)
# =========================================================
elif mode == "🖼️ Upload & AI Analysis":
    st.subheader("🖼️ Upload your artwork")
    st.write("Already have a drawing? Upload a PNG, JPG, JPEG, or WebP image, then choose whether you want a description or constructive feedback.")

    uploaded = st.file_uploader(
        "Choose an image",
        type=["png", "jpg", "jpeg", "webp"],
        key="analysis_image_upload",
    )

    image_bytes = None
    if uploaded is not None:
        try:
            image = Image.open(uploaded).convert("RGBA")
            st.image(image, caption="Your artwork", use_container_width=True)
            image_bytes = image_to_png_bytes(image)
        except Exception as error:
            st.error(f"Could not open this image: {error}")

    analysis_type = st.selectbox(
        "Choose your AI feedback",
        [
            "Detailed drawing analysis",
            "Describe what this image depicts",
        ],
        key="upload_analysis_type",
    )

    challenge_for_analysis = st.text_input(
        "Optional: What were you trying to draw?",
        value=st.session_state.get("challenge_text", ""),
        placeholder="For example: a house on a hill at sunset",
        key="challenge_for_upload",
    )

    if st.button("✨ Analyze My Artwork", type="primary", use_container_width=True):
        if not image_bytes:
            st.warning("Please upload an image first.")
        else:
            try:
                selected_type = "depict" if analysis_type == "Describe what this image depicts" else "general"
                result = run_analysis(
                    image_bytes,
                    challenge=challenge_for_analysis.strip() or None,
                    analysis_type=selected_type,
                    context="upload",
                )
                record_id = save_history(
                    user_id=CURRENT_USER["id"],
                    title=os.path.splitext(uploaded.name)[0] or "Uploaded Drawing",
                    mode="Uploaded Image",
                    challenge=challenge_for_analysis.strip(),
                    image_bytes=image_bytes,
                    analysis=result,
                )
                st.session_state["latest_history_id"] = record_id
                st.success("Analysis complete! Your drawing and feedback were saved in Drawing History.")
            except Exception as error:
                st.error(f"Analysis failed: {error}")

    if st.session_state.get("analysis_result") and st.session_state.get("analysis_context") == "upload":
        st.divider()
        with st.container(border=True):
            st.markdown("<div class='eyebrow'>YOUR AI ART COACH</div>", unsafe_allow_html=True)
            st.subheader("💡 Your AI Feedback")
            st.markdown(st.session_state["analysis_result"])

# =========================================================
# MODE 4: PERSONAL GALLERY
# =========================================================
elif mode == "🗂️ My Gallery":
    st.markdown("<div class='eyebrow'>YOUR PRIVATE ART COLLECTION</div>", unsafe_allow_html=True)
    st.subheader("🗂️ My Gallery")
    st.write("A home for the drawings you have saved or analyzed. Only drawings linked to your account appear here.")
    gallery_items = get_history(CURRENT_USER["id"], limit=100)
    has_saved_artwork = bool(gallery_items)
    if gallery_items:
        search_col, filter_col, sort_col = st.columns([2, 1, 1])
        with search_col:
            gallery_search = st.text_input(
                "Search your artwork",
                placeholder="Search by title or challenge...",
                key="gallery_search",
            ).strip().lower()
        with filter_col:
            gallery_filter = st.selectbox(
                "Artwork type",
                ["All artwork", "Challenges", "Creative canvas", "Uploads", "With AI feedback"],
                key="gallery_filter",
            )
        with sort_col:
            gallery_sort = st.selectbox(
                "Sort by",
                ["Newest first", "Oldest first", "Title A–Z"],
                key="gallery_sort",
            )

        filtered_items = []
        for item in gallery_items:
            search_blob = f"{item.get('title', '')} {item.get('challenge', '')} {item.get('mode', '')}".lower()
            if gallery_search and gallery_search not in search_blob:
                continue
            item_mode = item.get("mode", "")
            if gallery_filter == "Challenges" and "Challenge" not in item_mode:
                continue
            if gallery_filter == "Creative canvas" and item_mode != "Creative Canvas":
                continue
            if gallery_filter == "Uploads" and item_mode != "Uploaded Image":
                continue
            if gallery_filter == "With AI feedback" and not item.get("analysis"):
                continue
            filtered_items.append(item)

        if gallery_sort == "Oldest first":
            filtered_items.sort(key=lambda item: item.get("created_at", ""))
        elif gallery_sort == "Title A–Z":
            filtered_items.sort(key=lambda item: item.get("title", "").casefold())
        gallery_items = filtered_items

    if not gallery_items and not has_saved_artwork:
        st.markdown("""
        <div class="panel">
          <div class="eyebrow">YOUR GALLERY IS READY</div>
          <h3>Every masterpiece starts somewhere ✨</h3>
          <p>Make a drawing in Creative Canvas or complete a challenge, then choose Save Drawing or Analyze Drawing to add it here.</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("Tip: choose **Creative Canvas** from Workspace Navigation to make your first drawing.")
    elif not gallery_items:
        st.info("No artwork matches these search and filter settings. Try a different search or choose All artwork.")
    else:
        analyzed_count = sum(1 for item in gallery_items if item.get("analysis"))
        challenge_count = sum(1 for item in gallery_items if "Challenge" in item.get("mode", ""))
        metric_cols = st.columns(3)
        metric_cols[0].metric("Saved artworks", len(gallery_items))
        metric_cols[1].metric("AI feedback", analyzed_count)
        metric_cols[2].metric("Challenges", challenge_count)
        st.markdown("<div class='gallery-grid'>", unsafe_allow_html=True)
        cards = st.columns(3, gap="medium")
        for index, item in enumerate(gallery_items):
            with cards[index % 3]:
                record = get_history_item(item["id"], CURRENT_USER["id"])
                if not record:
                    continue
                st.markdown("<div class='gallery-card'>", unsafe_allow_html=True)
                st.image(bytes(record["image"]), use_container_width=True)
                st.markdown(f"**{item['title']}**")
                st.caption(f"{item['mode']} · {item['created_at']}")
                if item.get("analysis"):
                    st.markdown("<span class='gallery-tag'>✦ AI feedback saved</span>", unsafe_allow_html=True)
                if st.button("Open artwork", key=f"gallery_open_{item['id']}", use_container_width=True):
                    st.session_state["history_selected_id"] = item["id"]
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# MODE 5: COMPARE DRAWINGS
# =========================================================
elif mode == "🖼️ Compare Drawings":
    st.subheader("🖼️ Compare your creative ideas")
    st.write("Upload 2–10 drawings to ask AI for a side-by-side comparison. Use images you want to learn from, not as a score of your ability.")
    uploaded_files = st.file_uploader(
        "Choose 2 to 10 images to compare",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="comparison_uploads",
    )

    if uploaded_files:
        if len(uploaded_files) > 10:
            st.warning("Please select no more than 10 images.")
        else:
            columns = st.columns(min(len(uploaded_files), 3))
            for index, uploaded_file in enumerate(uploaded_files):
                with columns[index % len(columns)]:
                    st.image(uploaded_file, caption=f"Drawing {index + 1}", use_container_width=True)

            if len(uploaded_files) >= 2 and st.button("🔎 Compare My Drawings", type="primary", use_container_width=True):
                temp_paths = []
                try:
                    for uploaded_file in uploaded_files:
                        uploaded_file.seek(0)
                        image = Image.open(uploaded_file).convert("RGB")
                        temp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                        temp.close()
                        image.save(temp.name, format="PNG")
                        temp_paths.append(temp.name)
                    with st.spinner("✨ Comparing your artwork..."):
                        result = compare_drawings(temp_paths)
                    st.session_state["comparison_result"] = result
                except Exception as error:
                    st.error(f"Comparison failed: {error}")
                finally:
                    for path in temp_paths:
                        if os.path.exists(path):
                            os.remove(path)

    if st.session_state.get("comparison_result"):
        st.divider()
        st.subheader("📊 Your Comparison Results")
        st.markdown(st.session_state["comparison_result"])

# =========================================================
# FOLLOW-UP QUESTIONS ABOUT LAST ANALYZED DRAWING
# =========================================================
if st.session_state.get("last_drawing_bytes"):
    st.divider()
    with st.expander("💬 Ask AI About My Drawing"):
        st.write("Ask a follow-up question about the latest image you analyzed.")
        question = st.text_input(
            "Your question",
            placeholder="What detail could make my drawing more interesting?",
            key="drawing_followup_question",
        )
        if st.button("Ask My AI Art Coach", key="ask_drawing_ai"):
            if not question.strip():
                st.warning("Please enter a question first.")
            else:
                temp_path = None
                try:
                    temp_path = save_temp_image(st.session_state["last_drawing_bytes"])
                    history_text = "\n".join(
                        f"User: {item['question']}\nAI: {item['answer']}"
                        for item in st.session_state.get("drawing_questions", [])
                    )
                    with st.spinner("💭 Preparing your answer..."):
                        answer = ask_about_drawing(
                            image_path=temp_path,
                            question=question.strip(),
                            previous_analysis=st.session_state.get("last_drawing_analysis", ""),
                            conversation_history=history_text,
                        )
                    st.session_state["drawing_questions"].append(
                        {"question": question.strip(), "answer": answer}
                    )
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not get an answer: {error}")
                finally:
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)

        for item in st.session_state.get("drawing_questions", []):
            st.markdown(f"**You asked:** {item['question']}")
            st.markdown(f"**AI Art Coach:** {item['answer']}")

# =========================================================
# HISTORY PREVIEW
# =========================================================
selected_id = st.session_state.get("history_selected_id")
if selected_id:
    record = get_history_item(selected_id, CURRENT_USER["id"])
    if record:
        st.divider()
        st.subheader(f"🗂️ Saved drawing: {record['title']}")
        st.caption(f"{record['mode']} · {record['created_at']}")
        st.image(bytes(record["image"]), caption="Saved artwork", use_container_width=True)
        if record.get("challenge"):
            st.write(f"**Challenge:** {record['challenge']}")
        if record.get("analysis"):
            st.markdown("#### 🤖 Saved AI feedback")
            st.markdown(record["analysis"])
        if st.button("Close history preview"):
            st.session_state["history_selected_id"] = None
            st.rerun()

st.divider()
st.caption(
    "🌟 Create at your own pace. AI feedback is a helpful estimate, not an objective measure of artistic ability."
)
