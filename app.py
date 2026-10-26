
# =========================================================
# FINAL UI/UX POLISH — GLOBAL VISIBILITY & ACCESSIBILITY
# Place before the final st.divider() and st.caption().
# =========================================================
st.markdown(
    """
    <style>
    /* 1. Consistent typography and readable contrast */
    .stApp {
        color: #F5F6FF;
        font-size: 16px;
    }

    .stApp p,
    .stApp li,
    .stApp label,
    .stApp [data-testid="stCaptionContainer"] {
        line-height: 1.65;
    }

    .stApp p {
        color: #E0E5F6;
    }

    .stApp [data-testid="stCaptionContainer"] {
        color: #BCC7E5 !important;
    }

    .stApp h1 {
        font-size: clamp(1.9rem, 3vw, 2.7rem) !important;
        line-height: 1.2 !important;
        letter-spacing: -0.7px;
    }

    .stApp h2 {
        font-size: clamp(1.4rem, 2vw, 1.9rem) !important;
        line-height: 1.3 !important;
    }

    .stApp h3 {
        font-size: 1.2rem !important;
        line-height: 1.4 !important;
    }

    /* 2. Better reading width and section rhythm */
    .main .block-container {
        max-width: 1440px;
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        padding-left: clamp(1rem, 3vw, 2.5rem);
        padding-right: clamp(1rem, 3vw, 2.5rem);
    }

    [data-testid="stVerticalBlock"] {
        gap: 1rem;
    }

    [data-testid="stHorizontalBlock"] {
        gap: 1rem;
    }

    /* 3. Accessible form fields */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input {
        background: #F8FAFF !important;
        color: #17182B !important;
        border: 1px solid #9DA8C8 !important;
        border-radius: 10px !important;
        min-height: 44px;
    }

    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder {
        color: #606982 !important;
        opacity: 1;
    }

    [data-testid="stSelectbox"] [data-baseweb="select"] {
        border-radius: 10px;
        min-height: 44px;
    }

    /* 4. Clear, consistent buttons */
    .stApp div.stButton > button,
    .stApp [data-testid="stFormSubmitButton"] button,
    .stApp [data-testid="stLinkButton"] a {
        min-height: 44px;
        border-radius: 11px;
        font-weight: 650;
        line-height: 1.4;
        transition: border-color .15s ease,
                    background-color .15s ease;
    }

    .stApp div.stButton > button:focus-visible,
    .stApp [data-testid="stFormSubmitButton"] button:focus-visible,
    .stApp [data-testid="stLinkButton"] a:focus-visible {
        outline: 3px solid #BDA7FF !important;
        outline-offset: 3px;
    }

    /* 5. Distinguishable panels and messages */
    .stApp [data-testid="stAlert"] {
        border-radius: 12px;
        line-height: 1.6;
    }

    .stApp [data-testid="stExpander"] {
        border: 1px solid rgba(180, 190, 230, .30);
        border-radius: 14px;
        overflow: hidden;
    }

    .stApp [data-testid="stMetric"] {
        border-radius: 14px;
        padding: 16px;
    }

    /* 6. Sidebar: clear separation and comfortable targets */
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(180, 190, 230, .16);
    }

    [data-testid="stSidebar"] [data-testid="stButton"] button {
        min-height: 44px;
        text-align: left;
        line-height: 1.45;
    }

    /* 7. Image previews stay within their containers */
    .stApp [data-testid="stImage"] img {
        border-radius: 12px;
    }

    [data-testid="stFileUploader"] section {
        border-radius: 12px;
        border-style: dashed;
    }

    /* 8. Keyboard focus should remain visible */
    .stApp input:focus,
    .stApp textarea:focus {
        border-color: #9276ED !important;
        box-shadow: 0 0 0 2px rgba(146, 118, 237, .22) !important;
    }

    /* 9. Mobile: avoid cramped controls and horizontal overflow */
    @media (max-width: 700px) {
        .main .block-container {
            padding: 1rem .8rem 2rem;
        }

        .stApp h1 {
            font-size: 1.85rem !important;
        }

        .stApp h2 {
            font-size: 1.45rem !important;
        }

        .stApp div.stButton > button,
        .stApp [data-testid="stFormSubmitButton"] button {
            min-height: 46px;
        }

        [data-testid="stMetric"] {
            padding: 11px;
        }

        .stApp [data-testid="stImage"] {
            max-width: 100%;
        }
    }

    /* 10. Respect users who prefer reduced motion */
    @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
            animation-duration: .01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: .01ms !important;
            scroll-behavior: auto !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)
