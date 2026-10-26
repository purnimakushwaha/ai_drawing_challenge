import os
import re
import base64
import sqlite3
import tempfile
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from io import BytesIO

import streamlit as st
import streamlit.components.v1 as components
import extra_streamlit_components as stx
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

# Browser cookies keep a signed-in account or guest name on this device.
cookie_manager = stx.CookieManager(key="studio_cookie_manager")

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

    /* Professional UI refinement: hierarchy, readability, focus and spacing */
    [data-testid="stAppViewContainer"] .main .block-container {
        max-width: 1440px;
        padding-top: 1.6rem;
        padding-bottom: 2.5rem;
    }
    h1 { letter-spacing: -0.035em; line-height: 1.15; }
    h2, h3 { letter-spacing: -0.02em; line-height: 1.25; }
    p, li { line-height: 1.65; }
    [data-testid="stMarkdownContainer"] p { margin-bottom: .7rem; }
    [data-testid="stTextInput"] label,
    [data-testid="stTextArea"] label,
    [data-testid="stSelectbox"] label,
    [data-testid="stRadio"] > label,
    [data-testid="stFileUploader"] label {
        color: #edf0ff !important;
        font-weight: 600 !important;
    }
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input {
        background: rgba(12, 18, 38, .82) !important;
        color: #f7f8ff !important;
        border: 1px solid rgba(173, 183, 225, .32) !important;
        min-height: 42px;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stNumberInput"] input:focus {
        border-color: #b7a0ff !important;
        box-shadow: 0 0 0 2px rgba(151, 119, 255, .20) !important;
    }
    div.stButton > button,
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stLinkButton"] a {
        font-weight: 650;
        min-height: 43px;
        transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
    }
    div.stButton > button:focus-visible,
    [data-testid="stFormSubmitButton"] button:focus-visible,
    [data-testid="stLinkButton"] a:focus-visible {
        outline: 3px solid #c4b5fd !important;
        outline-offset: 3px !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { line-height: 1.5; }
    [data-testid="stHorizontalBlock"] { gap: 1rem; }
    [data-testid="stAlert"] { border-radius: 13px; }
    [data-testid="stImage"] img { border-radius: 12px; }
    @media (max-width: 700px) {
        [data-testid="stAppViewContainer"] .main .block-container {
            padding: 1rem .85rem 2rem;
        }
        [data-testid="stHorizontalBlock"] { gap: .55rem; }
    }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { transition-duration: .01ms !important; animation-duration: .01ms !important; }
    }
    @media (max-width: 700px) {
        .hero { padding: 20px 16px; }
        .hero h1 { font-size: 1.8rem; }
        .panel { padding: 16px; }
        .quick-start { grid-template-columns: 1fr; gap: 8px; }
        .quick-step { padding: 12px; }
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
    "history_edit_id": None,
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
            """CREATE TABLE IF NOT EXISTS remembered_sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )"""
        )
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


def _cookie_set(key, value):
    try:
        cookie_manager.set(key, value, expires_at=datetime.now() + timedelta(days=30))
    except Exception:
        # The current Streamlit session still works if browser cookies are blocked.
        pass


def remember_account(user):
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(HISTORY_DB) as connection:
        connection.execute("INSERT OR REPLACE INTO remembered_sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)", (token_hash, user["id"], expires))
        connection.commit()
    _cookie_set("studio_session", token)
    try:
        cookie_manager.delete("studio_guest_name")
    except Exception:
        pass
    st.session_state["current_user"] = user


def restore_remembered_user():
    try:
        cookies = cookie_manager.get_all() or {}
    except Exception:
        cookies = {}
    token = cookies.get("studio_session")
    if token:
        token_hash = hashlib.sha256(str(token).encode("utf-8")).hexdigest()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(HISTORY_DB) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT u.id, u.username, s.expires_at FROM remembered_sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=?",
                (token_hash,),
            ).fetchone()
            if row and row["expires_at"] >= now:
                st.session_state["current_user"] = {"id": row["id"], "username": row["username"], "is_guest": False}
                return
            connection.execute("DELETE FROM remembered_sessions WHERE token_hash=?", (token_hash,))
            connection.commit()
    guest_name = cookies.get("studio_guest_name")
    # When a guest explicitly chooses Sign in, do not immediately restore the guest cookie.
    if guest_name and not st.session_state.get("current_user") and not st.session_state.get("auth_return_to_login"):
        clean = re.sub(r"[^A-Za-z0-9 _.-]", "", str(guest_name)).strip()[:32]
        if clean:
            st.session_state["current_user"] = {"id": None, "username": clean, "is_guest": True}


def start_guest(name):
    clean = re.sub(r"\s+", " ", (name or "").strip())[:32]
    if len(clean) < 2:
        return False
    try:
        cookie_manager.delete("studio_session")
    except Exception:
        pass
    _cookie_set("studio_guest_name", clean)
    st.session_state["history_selected_id"] = None
    st.session_state["history_edit_id"] = None
    st.session_state["latest_history_id"] = None
    st.session_state["current_user"] = {"id": None, "username": clean, "is_guest": True}
    return True


def render_auth_screen():
    """Polished, responsive welcome screen with account and guest paths."""
    st.markdown("""
    <style>
    /* Authentication-only visual system */
    .auth-wrap{max-width:1120px;margin:8px auto 24px}
    .auth-brand{padding:30px 28px 26px;border:1px solid rgba(164,151,255,.22);border-radius:26px;
      background:radial-gradient(ellipse at 8% 0%,rgba(138,92,246,.24),transparent 42%),
      radial-gradient(ellipse at 100% 95%,rgba(57,164,211,.17),transparent 38%),
      linear-gradient(145deg,rgba(26,29,62,.98),rgba(15,25,48,.98));
      box-shadow:0 20px 55px rgba(0,0,0,.22);min-height:100%;}
    .auth-logo{display:inline-flex;align-items:center;gap:9px;padding:8px 12px;border-radius:13px;
      background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.10);color:#e6e1ff;
      font-weight:750;font-size:.82rem;letter-spacing:.25px}
    .auth-brand h1{font-size:clamp(2.05rem,4vw,3.15rem);line-height:1.07;letter-spacing:-1.6px;
      margin:25px 0 14px;color:#fff}
    .auth-brand h1 span{background:linear-gradient(90deg,#d9c5ff,#9bdcff);-webkit-background-clip:text;background-clip:text;color:transparent}
    .auth-brand p{font-size:.98rem;line-height:1.75;color:#cbd5ee;margin:0;max-width:470px}
    .auth-feature-list{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:25px}
    .auth-feature{padding:12px 13px;border-radius:14px;background:rgba(255,255,255,.045);
      border:1px solid rgba(205,199,255,.12);color:#e8eaff;font-size:.83rem;line-height:1.45}
    .auth-feature b{display:block;color:#fff;font-size:.87rem;margin-bottom:3px}
    .auth-side-title{font-size:.7rem;font-weight:800;letter-spacing:1.7px;color:#bfb0ff;text-transform:uppercase;margin-bottom:7px}
    .auth-panel-title{font-size:1.75rem;letter-spacing:-.6px;font-weight:780;color:#fff;line-height:1.2;margin:0 0 7px}
    .auth-panel-subtitle{font-size:.9rem;color:#bfc9e4;line-height:1.6;margin-bottom:19px}
    .auth-info{padding:11px 13px;border-radius:12px;background:rgba(67,83,132,.20);border:1px solid rgba(163,174,237,.17);
      color:#cdd7f1;font-size:.79rem;line-height:1.55;margin:14px 0 15px}
    .auth-guest{padding:17px 17px 14px;border:1px solid rgba(139,169,231,.22);border-radius:17px;
      background:rgba(31,49,82,.40);margin-top:18px}
    .auth-guest h3{font-size:1rem;color:#fff;margin:0 0 5px}
    .auth-guest p{font-size:.81rem;color:#bdc9e2;line-height:1.55;margin:0 0 12px}
    .auth-divider{display:flex;align-items:center;gap:10px;color:#8f9bbd;font-size:.72rem;letter-spacing:1.2px;margin:16px 0}
    .auth-divider:before,.auth-divider:after{content:'';height:1px;background:rgba(180,190,230,.18);flex:1}
    div[data-testid="stTextInput"] label{font-size:.84rem!important;font-weight:650!important;color:#e4e8f8!important}
    div[data-testid="stTextInput"] input{min-height:45px!important;border-radius:11px!important;background:rgba(8,14,31,.55)!important;border:1px solid rgba(163,174,224,.25)!important}
    div[data-testid="stTextInput"] input:focus{border-color:#9b85ff!important;box-shadow:0 0 0 2px rgba(155,133,255,.16)!important}
    div[data-testid="stForm"]{padding:0!important;border:0!important;background:transparent!important;margin:0!important}
    div[data-testid="stFormSubmitButton"] button,div.stButton>button{min-height:44px;border-radius:11px;font-weight:700;transition:all .16s ease}
    div[data-testid="stFormSubmitButton"] button[kind="primary"],div.stButton>button[kind="primary"]{border:0;background:linear-gradient(100deg,#8b6cf0,#5b91e9);color:white;box-shadow:0 7px 18px rgba(93,101,218,.19)}
    div[data-testid="stFormSubmitButton"] button:hover,div.stButton>button:hover{border-color:#b9a9ff;transform:translateY(-1px)}
    [data-testid="stAppViewContainer"] .main .block-container{padding-top:2rem;padding-bottom:2rem;max-width:1240px}
    @media(max-width:760px){.auth-brand{padding:23px 20px;border-radius:21px;margin-bottom:12px}.auth-brand h1{margin-top:19px}.auth-feature-list{gap:8px}.auth-feature{padding:10px;font-size:.78rem}.auth-panel-title{font-size:1.55rem}}
    @media(prefers-reduced-motion:reduce){*{transition:none!important}}
    </style>
    """, unsafe_allow_html=True)

    if st.session_state.pop("auth_return_to_login", False):
        st.session_state["auth_mode"] = "login"
    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "create"

    left, right = st.columns([1.02, 0.98], gap="large", vertical_alignment="top")
    with left:
        st.markdown("""
        <section class="auth-brand">
          <div class="auth-logo"><span style="font-size:1.25rem">✦</span> AI DRAWING STUDIO</div>
          <h1>Your imagination.<br/>Your <span>universe.</span></h1>
          <p>A creative space to sketch ideas, take on playful drawing challenges, and discover what your artwork can become.</p>
          <div class="auth-feature-list">
            <div class="auth-feature"><b>🎯 Creative quests</b>Fresh drawing prompts to spark ideas.</div>
            <div class="auth-feature"><b>🖌️ Open canvas</b>Draw freely, in your own style.</div>
            <div class="auth-feature"><b>✨ AI art coach</b>Get thoughtful, helpful feedback.</div>
            <div class="auth-feature"><b>🗂️ Your gallery</b>Keep your creations together.</div>
          </div>
        </section>
        <div class="auth-guest">
          <h3>Just want to explore?</h3>
          <p>Enter as a guest and start creating without setting up an account. Guest artwork is not saved to a personal account history.</p>
        </div>
        """, unsafe_allow_html=True)
        with st.form("guest_form"):
            guest_name = st.text_input("Your display name", max_chars=32, placeholder="What should we call you?")
            guest_submit = st.form_submit_button("Explore as Guest  →", use_container_width=True)
        if guest_submit:
            if start_guest(guest_name):
                st.rerun()
            else:
                st.error("Please enter a name with at least 2 characters.")

    with right:
        st.markdown('<div class="auth-side-title">YOUR CREATIVE SPACE</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-panel-title">Make room for ideas.</div><div class="auth-panel-subtitle">Create an account to keep your drawings and return to your studio anytime.</div>', unsafe_allow_html=True)
        tab_create, tab_login = st.columns(2, gap="small")
        with tab_create:
            if st.button("Create account", use_container_width=True, key="auth_create_tab", type="primary" if st.session_state["auth_mode"] == "create" else "secondary"):
                st.session_state["auth_mode"] = "create"
                st.rerun()
        with tab_login:
            if st.button("Log in", use_container_width=True, key="auth_login_tab", type="primary" if st.session_state["auth_mode"] == "login" else "secondary"):
                st.session_state["auth_mode"] = "login"
                st.rerun()

        if st.session_state["auth_mode"] == "create":
            st.markdown('<div class="auth-info">🔒 Use a username and password. Avoid including private personal information in your username.</div>', unsafe_allow_html=True)
            st.caption("Username: 3–32 characters · Password: at least 8 characters")
            with st.form("signup_form"):
                new_username = st.text_input("Choose a username", key="signup_username", placeholder="e.g. creative_artist")
                new_password = st.text_input("Create a password", type="password", key="signup_password", placeholder="At least 8 characters")
                confirm_password = st.text_input("Confirm password", type="password", key="signup_confirm_password", placeholder="Enter it again")
                submitted = st.form_submit_button("Create my studio  →", type="primary", use_container_width=True)
            if submitted:
                if new_password != confirm_password:
                    st.error("The passwords do not match.")
                else:
                    ok, result = create_account(new_username, new_password)
                    if ok:
                        remember_account({"id": result, "username": new_username.strip(), "is_guest": False})
                        st.success("Your studio is ready! Welcome to AI Drawing Studio.")
                        st.rerun()
                    else:
                        st.error(result)
        else:
            st.markdown('<div class="auth-info">🔐 Log in to reopen your personal gallery and continue where you left off.</div>', unsafe_allow_html=True)
            with st.form("login_form"):
                username = st.text_input("Username", key="login_username", placeholder="Your username")
                password = st.text_input("Password", type="password", key="login_password", placeholder="Your password")
                submitted = st.form_submit_button("Enter my studio  →", type="primary", use_container_width=True)
            if submitted:
                user = authenticate_user(username, password)
                if user:
                    remember_account({**user, "is_guest": False})
                    st.rerun()
                else:
                    st.error("Username or password is incorrect.")

    st.markdown('<div style="text-align:center;color:#8490b0;font-size:.75rem;margin:26px 0 0">MADE FOR CREATIVITY · TAKE YOUR TIME · MAKE SOMETHING YOURS</div>', unsafe_allow_html=True)


def save_history(user_id, title, mode, challenge, image_bytes, analysis=""):
    # Guests can draw and analyze, but never write to the persistent history table.
    if user_id is None:
        return None
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


def update_history_item(record_id, user_id, title, image_bytes):
    """Update an artwork only when it belongs to the signed-in user."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(HISTORY_DB) as connection:
        cursor = connection.execute(
            "UPDATE drawing_history SET title = ?, image = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (title.strip() or "My Creative Drawing", sqlite3.Binary(image_bytes), now, record_id, user_id),
        )
        connection.commit()
        return cursor.rowcount == 1



def rename_history_item(record_id, user_id, title):
    """Rename a saved artwork without changing its image or AI feedback."""
    clean_title = (title or "").strip()
    if not clean_title:
        return False
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(HISTORY_DB) as connection:
        cursor = connection.execute(
            "UPDATE drawing_history SET title = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (clean_title[:100], now, record_id, user_id),
        )
        connection.commit()
        return cursor.rowcount == 1

def delete_history_item(record_id, user_id):
    """Delete only the selected user's saved artwork."""
    with sqlite3.connect(HISTORY_DB) as connection:
        cursor = connection.execute(
            "DELETE FROM drawing_history WHERE id = ? AND user_id = ?", (record_id, user_id)
        )
        connection.commit()
        return cursor.rowcount == 1


# Initialise accounts/history before showing the login screen.
init_history_db()
if not st.session_state.get("current_user"):
    restore_remembered_user()
if not st.session_state.get("current_user"):
    render_auth_screen()
    st.stop()
CURRENT_USER = st.session_state["current_user"]
IS_GUEST = bool(CURRENT_USER.get("is_guest"))

# Return link opens the Creative Universe dashboard from the standalone app.
CREATIVE_UNIVERSE_URL = (
    os.environ.get("CREATIVE_UNIVERSE_URL", "").strip()
    or str(st.secrets.get("CREATIVE_UNIVERSE_URL", "")).strip()
)

# Persistent return navigation: the dashboard is opened in a separate browser tab,
# so browser history alone cannot reliably return the user to Creative Universe.
def render_return_to_universe():
    """Show a clear return link when the public dashboard URL is configured."""
    if CREATIVE_UNIVERSE_URL.startswith(("https://", "http://")):
        st.link_button(
            "🌌 Back to Creative Universe",
            CREATIVE_UNIVERSE_URL,
            use_container_width=True,
            help="Return to the Creative Universe project dashboard.",
        )
    else:
        st.caption("🌌 To enable Back to Creative Universe, set CREATIVE_UNIVERSE_URL in app Secrets.")

# Top-right navigation so users can always find their way back to the dashboard.
_nav_left, _nav_spacer, _nav_right = st.columns([2.2, 5, 2.5])
with _nav_left:
    st.markdown("<div style='padding-top:7px;color:#cbd5f0;font-size:.85rem;'>🎨 <b>AI Drawing Studio</b></div>", unsafe_allow_html=True)
with _nav_right:
    if CREATIVE_UNIVERSE_URL.startswith(("https://", "http://")):
        st.link_button("🌌 Back to Creative Universe", CREATIVE_UNIVERSE_URL, use_container_width=True)

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
                if IS_GUEST:
                    st.info("Guest mode: this drawing is not saved to history. Use the PNG button to download a copy, or create an account to keep your gallery.")
                else:
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
                if IS_GUEST:
                    st.info("AI analysis complete. Guest mode does not save history, so download your drawing if you want to keep a copy.")
                else:
                    st.success("AI analysis complete! Your drawing and feedback were saved in Drawing History.")
        except Exception as error:
            st.error(f"Could not process the drawing: {error}")

# =========================================================
# SIDEBAR: HISTORY
# =========================================================
with st.sidebar:
    if CREATIVE_UNIVERSE_URL.startswith(("https://", "http://")):
        st.link_button("🌌 Back to Creative Universe", CREATIVE_UNIVERSE_URL, use_container_width=True)
    else:
        st.info("To show the dashboard return button, add CREATIVE_UNIVERSE_URL to Streamlit Secrets.")
    st.divider()
    st.markdown(f"## 👋 {CURRENT_USER['username']}")
    if IS_GUEST:
        st.caption("Guest session · history is not saved")
        st.markdown(
            "<div style='padding:10px 12px;border:1px solid rgba(147,130,255,.35);"
            "border-radius:12px;background:linear-gradient(135deg,rgba(91,72,170,.22),"
            "rgba(36,102,145,.18));margin:8px 0 10px;'>"
            "<div style='font-weight:700;color:#e9e3ff;font-size:.92rem;'>Keep your artwork</div>"
            "<div style='color:#cbd5f0;font-size:.78rem;line-height:1.45;margin-top:4px;'>"
            "Sign in or create an account to save drawings and build your personal gallery.</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("🔐 Sign in / Create account", key="guest_signin_sidebar", use_container_width=True, type="primary"):
            try:
                cookie_manager.delete("studio_guest_name")
            except Exception:
                pass
            st.session_state["current_user"] = None
            st.session_state["auth_return_to_login"] = True
            st.session_state["auth_mode"] = "login"
            st.rerun()
    else:
        st.caption("Your account stays signed in on this device for up to 30 days.")
    if st.button("↪ Exit studio", use_container_width=True):
        try:
            cookies = cookie_manager.get_all() or {}
            token = cookies.get("studio_session")
            if token:
                token_hash = hashlib.sha256(str(token).encode("utf-8")).hexdigest()
                with sqlite3.connect(HISTORY_DB) as connection:
                    connection.execute("DELETE FROM remembered_sessions WHERE token_hash=?", (token_hash,))
                    connection.commit()
            cookie_manager.delete("studio_session")
            cookie_manager.delete("studio_guest_name")
        except Exception:
            pass
        st.session_state["current_user"] = None
        st.session_state["history_selected_id"] = None
        st.rerun()
    st.divider()
    st.markdown("## 🗂️ My Drawing History")
    if IS_GUEST:
        st.info("Guest drawings are not saved. Create an account or log in to keep a personal drawing history.")
        saved_items = []
    else:
        st.caption("Only your own saved drawings appear here. Click any drawing to open its full preview, edit it, or delete it.")
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
# HISTORY ITEM DETAIL PAGE (takes over the main view)
# =========================================================
selected_id = st.session_state.get("history_selected_id")
if selected_id:
    record = get_history_item(selected_id, CURRENT_USER["id"])
    if not record:
        st.session_state["history_selected_id"] = None
        st.session_state["history_edit_id"] = None
        st.warning("This drawing is no longer in your history.")
        st.rerun()

    back_col, title_col = st.columns([1, 4])
    with back_col:
        if st.button("← Back to Studio", key="history_back_to_studio", use_container_width=True):
            st.session_state["history_selected_id"] = None
            st.session_state["history_edit_id"] = None
            st.session_state["history_rename_id"] = None
            st.rerun()
    with title_col:
        st.markdown("### 🗂️ Your saved artwork")
        st.caption(f"{record['mode']}  ·  Created {record['created_at']}  ·  Updated {record['updated_at']}")

    # Keep the preview in a simple vertical reading order: artwork first,
    # then challenge details and AI feedback directly underneath it.
    st.markdown(f"## {record['title']}")
    image_col_left, image_col, image_col_right = st.columns([1, 3, 1], gap="medium")
    with image_col:
        st.image(bytes(record["image"]), caption=record["title"], use_container_width=True)

    if record.get("challenge"):
        st.markdown("#### 🎯 Drawing challenge")
        st.write(record["challenge"])

    st.markdown("#### 🤖 AI feedback")
    if record.get("analysis"):
        st.markdown(record["analysis"])
    else:
        st.caption("No AI feedback was saved for this drawing. Open a drawing tool and choose Analyze Drawing if you want feedback.")

    st.divider()
    action_rename, action_edit, action_delete = st.columns([1, 1, 1])
    with action_rename:
        if st.button("✏️ Rename", key=f"rename_history_{selected_id}", use_container_width=True):
            st.session_state["history_rename_id"] = selected_id
            st.rerun()
    with action_edit:
        if st.button("🖌️ Edit Drawing", key=f"edit_history_{selected_id}", use_container_width=True, type="primary"):
            st.session_state["history_edit_id"] = selected_id
            st.rerun()
    with action_delete:
        if st.button("🗑️ Delete", key=f"delete_history_{selected_id}", use_container_width=True):
            st.session_state["confirm_delete_history_id"] = selected_id
            st.rerun()

    if st.session_state.get("history_rename_id") == selected_id:
        with st.form(f"rename_history_form_{selected_id}"):
            st.markdown("#### ✏️ Rename this drawing")
            renamed_title = st.text_input("New drawing title", value=record["title"], max_chars=100, key=f"rename_title_input_{selected_id}")
            rename_save, rename_cancel = st.columns(2)
            with rename_save:
                submit_rename = st.form_submit_button("Save new title", type="primary", use_container_width=True)
            with rename_cancel:
                cancel_rename = st.form_submit_button("Cancel", use_container_width=True)
        if submit_rename:
            if not renamed_title.strip():
                st.error("Please enter a title before saving.")
            elif rename_history_item(selected_id, CURRENT_USER["id"], renamed_title):
                st.session_state["history_rename_id"] = None
                st.success("Drawing renamed successfully.")
                st.rerun()
            else:
                st.error("Could not rename this drawing. Please try again.")
        if cancel_rename:
            st.session_state["history_rename_id"] = None
            st.rerun()

    if st.session_state.get("confirm_delete_history_id") == selected_id:
        st.warning("Delete this saved drawing? This cannot be undone.")
        yes_col, no_col = st.columns(2)
        with yes_col:
            if st.button("Yes, delete drawing", key=f"confirm_delete_{selected_id}", type="primary", use_container_width=True):
                if delete_history_item(selected_id, CURRENT_USER["id"]):
                    st.session_state["history_selected_id"] = None
                    st.session_state["history_edit_id"] = None
                    st.session_state["confirm_delete_history_id"] = None
                    st.success("Drawing deleted from your history.")
                    st.rerun()
        with no_col:
            if st.button("Cancel", key=f"cancel_delete_{selected_id}", use_container_width=True):
                st.session_state["confirm_delete_history_id"] = None
                st.rerun()

    if st.session_state.get("history_edit_id") == selected_id:
        st.divider()
        st.markdown("## ✏️ Edit your saved drawing")
        st.info("To keep your original artwork safe, edit a copy in your preferred drawing app, then upload the updated image here. Saving replaces this history item instead of creating a duplicate.")
        with st.form(f"edit_history_form_{selected_id}"):
            edited_title = st.text_input("Drawing title", value=record["title"], max_chars=100)
            edited_file = st.file_uploader("Upload your edited artwork", type=["png", "jpg", "jpeg", "webp"], key=f"edited_artwork_{selected_id}")
            st.caption("Choose an edited image only if you want to replace the current saved artwork. Leave it empty to change just the title.")
            save_edits = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
        cancel_col, _ = st.columns([1, 3])
        with cancel_col:
            if st.button("Cancel editing", key=f"cancel_edit_{selected_id}", use_container_width=True):
                st.session_state["history_edit_id"] = None
                st.rerun()
        if save_edits:
            new_image = bytes(record["image"])
            if edited_file is not None:
                try:
                    opened = Image.open(edited_file)
                    opened.load()
                    new_image = image_to_png_bytes(opened)
                except Exception:
                    st.error("That image could not be opened. Please choose a valid PNG, JPG or WebP image.")
                    st.stop()
            if update_history_item(selected_id, CURRENT_USER["id"], edited_title, new_image):
                st.session_state["history_edit_id"] = None
                st.success("Your saved drawing has been updated.")
                st.rerun()
            else:
                st.error("Could not update this drawing. Please try again.")

    st.divider()
    st.caption("Your history is private to this signed-in account in this app's database.")
    st.stop()

# =========================================================
# POST-LOGIN DASHBOARD AND NAVIGATION
# =========================================================
import html

if CREATIVE_UNIVERSE_URL:
    st.link_button("← Back to Creative Universe", CREATIVE_UNIVERSE_URL, use_container_width=False)
else:
    st.caption("Tip: use your browser's Back button to return to Creative Universe, or set CREATIVE_UNIVERSE_URL in app settings to show a direct return button.")

mode = st.session_state.get("active_mode", "🏠 Home")
if mode != "🏠 Home":
    nav_col, _ = st.columns([1, 5])
    with nav_col:
        if st.button("← Back to dashboard", key="back_to_dashboard", use_container_width=True):
            st.session_state["active_mode"] = "🏠 Home"
            st.rerun()

if mode == "🏠 Home":
    saved_items = [] if IS_GUEST else get_history(CURRENT_USER["id"])
    total_drawings = len(saved_items)
    challenge_count = sum(1 for item in saved_items if "challenge" in (item.get("mode", "").lower()))
    upload_count = sum(1 for item in saved_items if "upload" in (item.get("mode", "").lower()))
    username_safe = html.escape(str(CURRENT_USER.get("username", "Artist")))

    st.markdown(
        f'''<section class="studio-hero">
          <div class="studio-hero-copy">
            <div class="studio-eyebrow"><span class="live-dot"></span> YOUR PERSONAL CREATIVE SPACE</div>
            <h1>Make room for<br><span>your imagination.</span></h1>
            <p>Welcome, <strong>{username_safe}</strong>. Start with a tiny idea, turn it into artwork, and let AI help you explore what comes next.</p>
            <div class="hero-tags"><span>✦ Create freely</span><span>✦ Try a challenge</span><span>✦ Keep your progress</span></div>
          </div>
          <div class="studio-hero-art" aria-hidden="true">
            <div class="orbit orbit-one"></div><div class="orbit orbit-two"></div>
            <div class="art-glow"></div><div class="art-spark spark-one">✦</div><div class="art-spark spark-two">✧</div>
            <div class="art-card"><div class="art-card-top"><span></span><span></span><span></span></div><div class="art-sun"></div><div class="art-mountain mountain-back"></div><div class="art-mountain mountain-front"></div><div class="art-wave"></div></div>
            <div class="floating-chip chip-top">✦ Idea to artwork</div><div class="floating-chip chip-bottom">🎨 Your next masterpiece</div>
          </div>
        </section>''',
        unsafe_allow_html=True,
    )
    if IS_GUEST:
        st.warning("You are browsing as a guest. Drawing history will not be saved, and it will not be available if you return later. Create an account or log in to keep your artwork and feedback.")

    st.markdown(r'''<style>
    .studio-hero{position:relative;overflow:hidden;display:grid;grid-template-columns:1.18fr .82fr;gap:18px;align-items:center;min-height:300px;padding:32px 34px;margin:0 0 26px;border-radius:26px;border:1px solid rgba(184,163,255,.28);background:radial-gradient(circle at 80% 45%,rgba(113,74,224,.30),transparent 35%),linear-gradient(120deg,rgba(39,30,79,.98),rgba(19,35,68,.97) 68%,rgba(20,43,73,.95));box-shadow:0 22px 55px rgba(3,5,20,.22)}
    .studio-hero:after{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(110deg,transparent 40%,rgba(164,143,255,.045),transparent 75%)}
    .studio-hero-copy{position:relative;z-index:2}.studio-eyebrow{font-size:.72rem;font-weight:800;letter-spacing:1.8px;color:#c7b4ff;margin-bottom:16px}.live-dot{display:inline-block;width:7px;height:7px;margin:0 8px 1px 0;border-radius:50%;background:#9ce9cf;box-shadow:0 0 12px #75e3c3}
    .studio-hero h1{font-size:clamp(2rem,3.5vw,3.2rem);line-height:1.05;letter-spacing:-1.5px;margin:0 0 14px;color:#fff}.studio-hero h1 span{background:linear-gradient(90deg,#d6c2ff,#91c5ff);-webkit-background-clip:text;background-clip:text;color:transparent}.studio-hero p{max-width:570px;font-size:1rem;line-height:1.7;color:#d1d6ef;margin:0}.studio-hero p strong{color:#fff}.hero-tags{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}.hero-tags span{font-size:.76rem;color:#e4ddff;background:rgba(179,157,255,.10);border:1px solid rgba(185,164,255,.18);border-radius:999px;padding:7px 10px}
    .studio-hero-art{position:relative;min-height:230px;display:flex;align-items:center;justify-content:center}.orbit{position:absolute;width:250px;height:250px;border:1px solid rgba(174,160,255,.18);border-radius:50%;transform:rotate(-28deg) scaleY(.65)}.orbit-two{width:300px;height:300px;transform:rotate(35deg) scaleY(.58);border-color:rgba(111,183,255,.17)}.art-glow{position:absolute;width:200px;height:160px;border-radius:50%;background:rgba(115,74,234,.32);filter:blur(35px)}.art-card{position:relative;z-index:1;width:180px;height:190px;overflow:hidden;border-radius:17px;border:1px solid rgba(255,255,255,.45);background:linear-gradient(155deg,#f7c9dc,#9b8df2 53%,#314a94);box-shadow:0 18px 40px rgba(3,5,20,.4);transform:rotate(5deg)}.art-card-top{position:absolute;z-index:5;top:10px;left:11px;display:flex;gap:4px}.art-card-top span{width:5px;height:5px;border-radius:50%;background:rgba(35,25,70,.55)}.art-sun{position:absolute;top:35px;right:28px;width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#fff1b8,#ffb8cb);box-shadow:0 0 28px rgba(255,222,192,.55)}.art-mountain{position:absolute;bottom:32px;width:0;height:0;border-left:105px solid transparent;border-right:105px solid transparent}.mountain-back{left:-25px;border-bottom:105px solid #5b58ac}.mountain-front{left:28px;border-bottom:82px solid #303f80}.art-wave{position:absolute;bottom:-23px;left:-15px;width:220px;height:65px;border-radius:50% 50% 0 0;background:#1c315d;transform:rotate(-8deg)}.art-spark{position:absolute;color:#e1d3ff;font-size:25px;z-index:2}.spark-one{top:26px;right:35px}.spark-two{bottom:26px;left:28px;font-size:20px}.floating-chip{position:absolute;z-index:3;font-size:.72rem;font-weight:700;color:#f1edff;padding:9px 12px;border:1px solid rgba(202,187,255,.25);border-radius:12px;background:rgba(22,23,55,.82);box-shadow:0 8px 22px rgba(0,0,0,.18);backdrop-filter:blur(10px)}.chip-top{top:20px;left:0}.chip-bottom{bottom:17px;right:0}
    .dashboard-section-title{font-size:1.32rem;font-weight:800;letter-spacing:-.35px;color:#f6f3ff;margin:4px 0 3px}.dashboard-section-copy{font-size:.9rem;color:#bfc7e4;margin:0 0 15px}.stat-card{position:relative;overflow:hidden;padding:17px 18px;border-radius:18px;background:linear-gradient(145deg,rgba(37,38,78,.85),rgba(21,31,59,.88));border:1px solid rgba(165,157,230,.20);min-height:108px}.stat-card:after{content:"";position:absolute;right:-20px;top:-35px;width:95px;height:95px;border-radius:50%;background:rgba(131,94,226,.10)}.stat-label{font-size:.78rem;color:#bfc7e5;margin-bottom:9px}.stat-value{font-size:1.75rem;line-height:1;font-weight:800;color:#fff}.stat-note{font-size:.72rem;color:#9da9d2;margin-top:8px}.activity-card{position:relative;min-height:176px;padding:20px 19px 17px;border-radius:20px;background:linear-gradient(150deg,rgba(37,35,76,.92),rgba(19,31,58,.94));border:1px solid rgba(166,153,235,.21);box-shadow:0 10px 28px rgba(2,5,20,.13);margin-bottom:9px;transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease}.activity-card:hover{border-color:rgba(190,169,255,.55);transform:translateY(-3px);box-shadow:0 15px 34px rgba(2,5,20,.22)}.activity-card .activity-icon{width:48px;height:48px;display:flex;align-items:center;justify-content:center;border-radius:15px;font-size:1.5rem;margin-bottom:15px;background:linear-gradient(135deg,rgba(143,100,239,.27),rgba(72,140,229,.20));border:1px solid rgba(189,167,255,.22)}.activity-card h3{font-size:1.03rem;margin:0 0 7px;color:#f5f1ff}.activity-card p{font-size:.86rem;line-height:1.55;color:#c4cce6;margin:0}.activity-kicker{font-size:.67rem;letter-spacing:1.1px;text-transform:uppercase;color:#bba8ff;font-weight:800;margin-bottom:7px}
    /* Full-card interaction styling */
    div[class*="st-key-dashboard_"] button {
        position: relative !important; overflow: hidden !important;
        min-height: 174px !important; height: auto !important; width: 100%;
        display: flex; align-items: flex-start; justify-content: flex-start; text-align: left;
        white-space: pre-wrap !important; line-height: 1.48 !important;
        padding: 21px 100px 20px 20px !important; border-radius: 20px !important;
        color: #f5f1ff !important; font-size: .91rem !important; font-weight: 500 !important;
        background: linear-gradient(145deg,rgba(39,36,82,.98),rgba(17,31,58,.98)) !important;
        border: 1px solid rgba(166,153,235,.30) !important;
        box-shadow: 0 10px 28px rgba(2,5,20,.13) !important;
        transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
    }
    /* A different decorative mini-illustration on each fully clickable card. */
    div[class*="st-key-dashboard_ai_drawing_challenge"] button::after,
    div[class*="st-key-dashboard_creative_canvas"] button::after,
    div[class*="st-key-dashboard_upload_and_ai_analysis"] button::after,
    div[class*="st-key-dashboard_compare_drawings"] button::after {
        position: absolute; right: 16px; top: 22px; width: 76px; height: 76px;
        display: flex; align-items: center; justify-content: center;
        border-radius: 24px; font-size: 2.55rem; line-height: 1;
        border: 1px solid rgba(211,200,255,.24);
        box-shadow: inset 0 1px 0 rgba(255,255,255,.12), 0 9px 25px rgba(3,6,25,.22);
        pointer-events: none;
    }
    div[class*="st-key-dashboard_ai_drawing_challenge"] button::after {
        content: "🎯"; background: radial-gradient(circle at 30% 20%,rgba(255,194,129,.35),transparent 55%),linear-gradient(145deg,#51428d,#253c70);
    }
    div[class*="st-key-dashboard_creative_canvas"] button::after {
        content: "🖌️"; background: radial-gradient(circle at 30% 20%,rgba(255,190,223,.35),transparent 55%),linear-gradient(145deg,#704d9b,#263f78);
    }
    div[class*="st-key-dashboard_upload_and_ai_analysis"] button::after {
        content: "🖼️"; background: radial-gradient(circle at 30% 20%,rgba(144,221,255,.35),transparent 55%),linear-gradient(145deg,#326c91,#29376f);
    }
    div[class*="st-key-dashboard_compare_drawings"] button::after {
        content: "✨"; background: radial-gradient(circle at 30% 20%,rgba(255,226,141,.35),transparent 55%),linear-gradient(145deg,#76528f,#293f77);
    }
    div[class*="st-key-dashboard_"] button:hover {
        border-color: rgba(190,169,255,.75) !important;
        box-shadow: 0 15px 34px rgba(2,5,20,.24) !important;
        transform: translateY(-2px);
    }
    .dashboard-tip{border-radius:16px;padding:15px 17px;margin:12px 0 18px;background:linear-gradient(100deg,rgba(96,67,164,.20),rgba(37,87,145,.14));border:1px solid rgba(164,158,255,.21);color:#e2e7ff;line-height:1.6}
    @media(max-width:850px){.studio-hero{grid-template-columns:1fr;padding:25px 23px}.studio-hero-art{min-height:205px}.studio-hero h1{font-size:2.2rem}.activity-card{min-height:155px}div[class*="st-key-dashboard_"] button{padding-right:88px!important;min-height:160px!important}div[class*="st-key-dashboard_ai_drawing_challenge"] button::after,div[class*="st-key-dashboard_creative_canvas"] button::after,div[class*="st-key-dashboard_upload_and_ai_analysis"] button::after,div[class*="st-key-dashboard_compare_drawings"] button::after{width:62px;height:62px;right:12px;top:18px;font-size:2rem;border-radius:19px}}
    @media(prefers-reduced-motion:reduce){.activity-card{transition:none}.activity-card:hover{transform:none}}
    </style>''', unsafe_allow_html=True)

    st.markdown('<div class="dashboard-section-title">Your creative overview</div><div class="dashboard-section-copy">Every sketch is progress. Here is how your studio is growing.</div>', unsafe_allow_html=True)
    metric_cols = st.columns(3, gap="medium")
    metrics = [
        ("✦  SAVED ARTWORKS", total_drawings, "Your creative collection"),
        ("◎  CHALLENGE DRAWINGS", challenge_count, "Ideas turned into quests"),
        ("▧  UPLOADED ARTWORKS", upload_count, "Artwork reviewed by AI"),
    ]
    for col, (label, value, note) in zip(metric_cols, metrics):
        with col:
            st.markdown(f'<div class="stat-card"><div class="stat-label">{label}</div><div class="stat-value">{value}</div><div class="stat-note">{note}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="dashboard-section-title" style="margin-top:26px">What would you like to create?</div><div class="dashboard-section-copy">Choose a path. You can switch activities whenever you like.</div>', unsafe_allow_html=True)
    activities = [
        ("🎯", "AI Drawing Challenge", "GET INSPIRED", "A fresh drawing quest, with a difficulty that fits your mood.", "🎯 AI Drawing Challenge", "Start a challenge"),
        ("🪄", "Creative Canvas", "YOUR BLANK CANVAS", "A blank canvas for anything you imagine.", "🪄 Creative Canvas", "Open the canvas"),
        ("🖼️", "Upload & AI Analysis", "A FRESH PERSPECTIVE", "Upload your art for helpful AI feedback.", "🖼️ Upload & AI Analysis", "Analyze artwork"),
        ("🧩", "Compare Drawings", "SEE THE DIFFERENCE", "View two drawings side by side and compare them with AI.", "🖼️ Compare Drawings", "Compare artwork"),
    ]
    # The entire activity card is a real button, not decorative HTML.
    for row_start in (0, 2):
        cols = st.columns(2, gap="medium")
        for col, (emoji, title, kicker, description, option, button_label) in zip(cols, activities[row_start:row_start+2]):
            with col:
                card_label = f"{emoji}  {title}\n{kicker}  ·  {description}\n{button_label}  →"
                if st.button(
                    card_label,
                    key=f"dashboard_{title.lower().replace(' ', '_').replace('&', 'and')}",
                    type="secondary",
                    use_container_width=True,
                ):
                    st.session_state["active_mode"] = option
                    st.rerun()

    if total_drawings:
        latest = saved_items[0]
        latest_title = html.escape(str(latest.get("title", "Untitled artwork")))
        st.markdown(f'<div class="dashboard-tip">✦ <strong>Your creative journey continues:</strong> Your latest saved artwork is <strong>{latest_title}</strong>. Open it from <em>My Drawing History</em> in the sidebar.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="dashboard-tip">🌱 <strong>Your gallery is ready for its first creation.</strong> Start with a challenge or open the blank canvas. Save your artwork to build your personal collection.</div>', unsafe_allow_html=True)

    # =========================================================

# MODE 1: AI DRAWING CHALLENGE
# =========================================================
elif mode == "🎯 AI Drawing Challenge":
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
                if IS_GUEST:
                    st.info("Analysis complete. Guest mode does not save history; download your drawing to keep a copy.")
                else:
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

st.divider()
st.caption(
    "🌟 Create at your own pace. AI feedback is a helpful estimate, not an objective measure of artistic ability."
)
