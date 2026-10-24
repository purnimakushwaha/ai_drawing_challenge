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
    :root { --bg:#0a0b16; --panel:#15172a; --panel2:#1c1e36; --line:rgba(177,157,255,.20); --muted:#aaaecb; --text:#f7f5ff; --purple:#9165ff; --blue:#548dff; }
    .stApp { background: radial-gradient(ellipse at 12% 0%,rgba(105,63,211,.22),transparent 35%), radial-gradient(ellipse at 95% 20%,rgba(42,111,220,.16),transparent 32%), linear-gradient(135deg,#090b16,#101127 56%,#0b1324); color:var(--text); }
    [data-testid="stHeader"] { background:rgba(8,10,22,.55); }
    [data-testid="stSidebar"] { background:linear-gradient(180deg,#111326,#0e1222); border-right:1px solid rgba(177,157,255,.13); }
    [data-testid="stSidebar"] > div:first-child { padding-top:1.25rem; }
    h1,h2,h3,h4 { color:var(--text)!important; letter-spacing:-.035em; }
    p, label, li, [data-testid="stMarkdownContainer"] { color:#d9d9ee; }
    [data-testid="stCaptionContainer"] { color:var(--muted); }
    .block-container { max-width:1500px; padding-top:2rem; padding-bottom:3rem; }
    .brand-row { display:flex; align-items:center; gap:13px; margin-bottom:18px; }
    .brand-mark { width:48px;height:48px;display:flex;align-items:center;justify-content:center;border-radius:15px;background:linear-gradient(135deg,#9b6aff,#477dff);font-size:25px;box-shadow:0 8px 28px rgba(116,81,255,.28); }
    .brand-name { font-size:1.15rem;font-weight:800;letter-spacing:.02em;color:#fff; }
    .brand-sub { font-size:.78rem;color:#a9accb;margin-top:2px; }
    .hero { position:relative; overflow:hidden; padding:34px 34px 31px; border-radius:25px; background:linear-gradient(115deg,rgba(105,62,202,.36),rgba(40,77,151,.25) 60%,rgba(22,26,51,.65)); border:1px solid rgba(187,167,255,.24); box-shadow:0 18px 50px rgba(0,0,0,.15); margin:4px 0 24px; }
    .hero:after { content:'✦'; position:absolute; right:7%;top:4%;font-size:5rem;color:rgba(220,209,255,.10); }
    .hero h1 { margin:8px 0 10px;font-size:clamp(2rem,4vw,3.25rem);line-height:1.08;letter-spacing:-.055em; }
    .hero p { max-width:780px; margin:0;color:#d4d8f3;line-height:1.75;font-size:1rem; }
    .eyebrow { color:#c5afff;font-size:.72rem;font-weight:800;letter-spacing:1.8px;text-transform:uppercase; }
    .panel,.quick-step { padding:21px;border-radius:19px;background:linear-gradient(145deg,rgba(28,30,57,.93),rgba(19,23,43,.94));border:1px solid var(--line);margin:12px 0 18px; }
    .notice { padding:14px 17px;border-radius:14px;background:rgba(83,91,160,.14);border:1px solid rgba(157,158,255,.20);color:#e3e5ff;line-height:1.65;margin:12px 0 18px; }
    .quick-start { display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px;margin:10px 0 24px; }
    .quick-step { margin:0;padding:17px 18px; }
    .quick-step strong { display:block;margin-bottom:6px;color:#fff;font-size:.98rem; }
    .quick-step span { color:#bfc4e2;font-size:.88rem;line-height:1.55; }
    div.stButton > button,[data-testid="stFormSubmitButton"] button,[data-testid="stLinkButton"] a { border-radius:12px!important;min-height:44px;font-weight:650;transition:all .18s ease;border:1px solid rgba(178,162,255,.23); }
    div.stButton > button[kind="primary"],[data-testid="stFormSubmitButton"] button[kind="primary"] { background:linear-gradient(100deg,#8c5cff,#4e82ff)!important;color:#fff!important;border:0!important;box-shadow:0 7px 20px rgba(100,78,230,.2); }
    div.stButton > button:hover { transform:translateY(-1px);border-color:#bba7ff!important;box-shadow:0 7px 20px rgba(80,70,160,.15); }
    [data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stSelectbox"] [data-baseweb="select"],[data-testid="stNumberInput"] input { border-radius:11px!important;background-color:rgba(12,15,31,.75); }
    [data-testid="stFileUploader"] section { border:1px dashed rgba(174,153,255,.48);border-radius:16px;background:rgba(29,30,61,.38); }
    [data-testid="stMetric"] { background:linear-gradient(145deg,rgba(37,35,72,.85),rgba(22,26,48,.88));padding:17px;border-radius:17px;border:1px solid rgba(165,151,255,.20); }
    [data-testid="stMetricLabel"] { color:#b8bcdb!important; }
    [data-testid="stMetricValue"] { color:#fff!important; }
    [data-testid="stExpander"] { border:1px solid var(--line);border-radius:15px;background:rgba(22,24,47,.48); }
    [data-testid="stRadio"] > div { gap:8px; }
    [data-testid="stRadio"] label { background:rgba(35,37,70,.62);border:1px solid rgba(166,146,255,.18);border-radius:12px;padding:9px 12px; }
    [data-testid="stTabs"] button { color:#c9c7e5!important; }
    [data-testid="stTabs"] button[aria-selected="true"] { color:#fff!important;border-bottom-color:#a78bfa!important; }
    [data-testid="stSidebar"] [data-testid="stButton"] button { text-align:left; }
    hr { border-color:rgba(171,161,226,.14)!important; }
    .auth-wrap { display:grid;grid-template-columns:1.05fr .95fr;gap:22px;align-items:stretch;margin-top:14px; }
    .auth-art { min-height:520px;padding:36px;border-radius:25px;background:radial-gradient(circle at 80% 18%,rgba(113,77,255,.42),transparent 30%),radial-gradient(circle at 15% 85%,rgba(45,132,255,.26),transparent 32%),linear-gradient(145deg,#211746,#121b38 72%,#111326);border:1px solid rgba(189,170,255,.24);display:flex;flex-direction:column;justify-content:space-between; }
    .auth-art h1 { font-size:clamp(2.2rem,4vw,3.5rem);line-height:1.06;margin:18px 0 12px; }
    .art-orbit { height:190px;display:flex;align-items:center;justify-content:center;font-size:7rem;text-shadow:0 0 45px rgba(165,127,255,.7); }
    .auth-card { padding:28px;border-radius:25px;background:linear-gradient(145deg,rgba(27,29,55,.98),rgba(17,21,40,.98));border:1px solid rgba(179,160,255,.20); }
    .section-hint { color:#c4c7e4;margin-top:-5px;margin-bottom:14px; }
    @media(max-width:850px) { .auth-wrap{grid-template-columns:1fr}.auth-art{min-height:330px;padding:25px}.art-orbit{height:100px;font-size:4.5rem}.hero{padding:24px 20px}.quick-start{grid-template-columns:1fr}.block-container{padding-top:1rem} }
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
    art_col, form_col = st.columns([1.05, .95], gap="large")
    with art_col:
        st.markdown("""
        <div class="auth-art">
          <div>
            <div class="brand-row"><div class="brand-mark">✦</div><div><div class="brand-name">AI DRAWING STUDIO</div><div class="brand-sub">Your creative universe</div></div></div>
            <div class="eyebrow">IMAGINE · DRAW · DISCOVER</div>
            <h1>Your ideas deserve<br>to come alive.</h1>
            <p style="color:#d4d7f4;line-height:1.75;max-width:470px">A personal creative space to sketch freely, try playful challenges, and get thoughtful feedback from your AI art coach.</p>
          </div>
          <div class="art-orbit">🎨 ✦</div>
          <div style="color:#c7c6e8;font-size:.9rem">One canvas. Endless possibilities.</div>
        </div>
        """, unsafe_allow_html=True)
    with form_col:
        st.markdown("<div class='eyebrow'>WELCOME TO YOUR STUDIO</div>", unsafe_allow_html=True)
        st.markdown("## Create something wonderful")
        st.markdown("<p style='color:#bfc3df;line-height:1.65'>Log in to continue your creative journey, or create an account to keep your artwork private and saved.</p>", unsafe_allow_html=True)
        login_tab, signup_tab = st.tabs(["Log in", "Create account"])
        with login_tab:
            with st.form("login_form"):
                username = st.text_input("Username", key="login_username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
                submitted = st.form_submit_button("Log in to Studio →", type="primary", use_container_width=True)
            if submitted:
                user = authenticate_user(username, password)
                if user:
                    st.session_state["current_user"] = user
                    st.rerun()
                else:
                    st.error("Username or password is incorrect.")
        with signup_tab:
            st.caption("Use 3–32 characters for your username and at least 8 characters for your password.")
            with st.form("signup_form"):
                new_username = st.text_input("Create username", key="signup_username", placeholder="Choose a username")
                new_password = st.text_input("Create password", type="password", key="signup_password", placeholder="At least 8 characters")
                confirm_password = st.text_input("Confirm password", type="password", key="signup_confirm_password", placeholder="Repeat your password")
                submitted = st.form_submit_button("Create my account →", type="primary", use_container_width=True)
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
    st.markdown("<div class='notice'>🔒 Your saved drawings are associated with your account. Your password is stored as a salted hash, not plain text.</div>", unsafe_allow_html=True)


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
    st.markdown("<div class='brand-row'><div class='brand-mark'>✦</div><div><div class='brand-name'>ARTSPACE AI</div><div class='brand-sub'>Your creative universe</div></div></div>", unsafe_allow_html=True)
    st.markdown(f"### 👋 {CURRENT_USER['username']}")
    st.caption("Your personal studio")
    if st.button("↪ Log out", use_container_width=True):
        st.session_state["current_user"] = None
        st.session_state["history_selected_id"] = None
        st.rerun()
    st.divider()
    st.markdown("#### YOUR LIBRARY")
    st.caption("Saved drawings and feedback are private to your account.")
    saved_items = get_history(CURRENT_USER["id"])
    if not saved_items:
        st.info("Your gallery is waiting for its first creation. Save a drawing to see it here.")
    else:
        for item in saved_items:
            if st.button(f"🎨  {item['title'][:25]}", key=f"history_{item['id']}", use_container_width=True, help=f"{item['mode']} · {item['created_at']}"):
                st.session_state["history_selected_id"] = item["id"]
                st.rerun()

# =========================================================
# HEADER AND NAVIGATION
# =========================================================
st.markdown(
    f"""
    <div class="hero">
      <div class="eyebrow">YOUR PERSONAL CREATIVE SPACE</div>
      <h1>Welcome back, {CURRENT_USER['username']} ✦</h1>
      <p>Make something only you could imagine. Start with a fresh canvas, take on an AI-powered challenge, or revisit artwork from your library.</p>
    </div>
    <div class="quick-start">
      <div class="quick-step"><strong>✦ Find your spark</strong><span>Generate a creative prompt or bring your own idea.</span></div>
      <div class="quick-step"><strong>✎ Make it yours</strong><span>Draw freely with your own style and pace.</span></div>
      <div class="quick-step"><strong>✧ Grow with feedback</strong><span>Save your work and ask your AI art coach what to try next.</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

mode = st.selectbox(
    "What would you like to do today?",
    [
        "🎯 AI Drawing Challenge",
        "🪄 Creative Canvas",
        "🖼️ Upload & AI Analysis",
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
        st.subheader("💡 Your AI Feedback")
        st.markdown(st.session_state["analysis_result"])

# =========================================================
# MODE 4: COMPARE DRAWINGS
# =========================================================
else:
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
