"""
Streamlit frontend for the Smart Data Analysis Platform.
Talks to the FastAPI backend for upload, EDA, and natural language Q&A.
"""
import base64
import io

import requests
import streamlit as st
from PIL import Image

# Change this to your Render URL once deployed (e.g. "https://your-app.onrender.com")
BACKEND_URL = "https://betabytez-aiml-task5-ummehabiba.onrender.com"

st.set_page_config(page_title="Smart Data Analysis Platform", layout="wide", page_icon="⚡")

# ---------------------------------------------------------------------------
# THEME — dark violet/magenta, bold display type, glowing accents
# ---------------------------------------------------------------------------
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700;900&family=Inter:wght@400;500;600&display=swap');

:root {
    --bg-deep: #0B0714;
    --bg-mid: #1A0B2E;
    --accent-violet: #B026FF;
    --accent-magenta: #FF2FD4;
    --text-primary: #FFFFFF;
    --text-secondary: #E8DFFF;
    --card-bg: rgba(255, 255, 255, 0.04);
    --card-border: rgba(176, 38, 255, 0.35);
}

.stApp {
    background: radial-gradient(ellipse 120% 80% at 50% -10%, var(--bg-mid) 0%, var(--bg-deep) 55%);
    color: var(--text-primary);
}

/* Hero title block */
.hero-wrap {
    position: relative;
    padding: 3rem 0 2rem 0;
    text-align: center;
    overflow: visible;
}
.hero-glow {
    position: absolute;
    top: -60px;
    left: 50%;
    transform: translateX(-50%);
    width: 480px;
    height: 480px;
    background: radial-gradient(circle, rgba(176,38,255,0.35) 0%, rgba(255,47,212,0.15) 45%, transparent 70%);
    filter: blur(10px);
    z-index: 0;
    pointer-events: none;
}
.hero-eyebrow {
    position: relative;
    z-index: 1;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    font-size: 0.8rem;
    color: var(--accent-magenta);
    margin-bottom: 0.75rem;
}
.hero-title {
    position: relative;
    z-index: 1;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 900;
    font-size: clamp(2.8rem, 6vw, 5rem);
    line-height: 1.0;
    letter-spacing: -0.02em;
    background: linear-gradient(120deg, #FFFFFF 20%, var(--accent-violet) 60%, var(--accent-magenta) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
}
.hero-sub {
    position: relative;
    z-index: 1;
    font-family: 'Inter', sans-serif;
    font-size: 1.1rem;
    color: var(--text-secondary);
    margin-top: 1rem;
    max-width: 640px;
    margin-left: auto;
    margin-right: auto;
}

/* Section headers */
.section-label {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.6rem;
    color: var(--text-primary);
    margin-top: 2.5rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.section-label .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent-violet), var(--accent-magenta));
    box-shadow: 0 0 12px var(--accent-magenta);
    display: inline-block;
}

/* Card container look for file uploader / results */
[data-testid="stFileUploader"], .result-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 1.2rem;
    backdrop-filter: blur(6px);
}

/* Buttons */
.stButton > button {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    letter-spacing: 0.02em;
    background: linear-gradient(135deg, var(--accent-violet), var(--accent-magenta));
    color: white;
    border: none;
    border-radius: 999px;
    padding: 0.6rem 1.8rem;
    box-shadow: 0 0 18px rgba(255, 47, 212, 0.35);
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.stButton > button:hover {
    box-shadow: 0 0 28px rgba(255, 47, 212, 0.6);
    transform: translateY(-1px);
    color: white;
}

/* Text input — target all nested wrapper layers */
div[data-testid="stTextInput"] > div,
div[data-testid="stTextInput"] > div > div,
div[data-baseweb="input"],
div[data-baseweb="base-input"] {
    background: var(--card-bg) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 12px !important;
}
div[data-testid="stTextInput"] input {
    background: transparent !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    caret-color: var(--accent-magenta) !important;
}
div[data-testid="stTextInput"] input::placeholder {
    color: var(--text-secondary) !important;
    opacity: 0.6;
}

/* Success / info / error boxes */
div[data-testid="stAlert"] {
    border-radius: 12px;
    font-family: 'Inter', sans-serif;
}

/* General body text */
p, span, label, .stMarkdown {
    font-family: 'Inter', sans-serif;
}

/* Caption under hero */
.stCaption {
    color: var(--text-secondary) !important;
}

/* Remove Streamlit's default white header bar */
[data-testid="stHeader"] {
    background: transparent;
}
[data-testid="stToolbar"] {
    display: none;
}
</style>
"""

st.markdown(THEME_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# HERO
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero-wrap">
        <div class="hero-glow"></div>
        <div class="hero-eyebrow">Upload → Analyze → Ask</div>
        <div class="hero-title">SMART DATA<br/>ANALYSIS</div>
        <div class="hero-sub">Drop in a CSV and get instant EDA, live charts, and answers to
        plain-English questions about your data — no code required.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Session state holds the current session_id across Streamlit reruns
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "df_info" not in st.session_state:
    st.session_state.df_info = None


def show_figures(figures_b64: list):
    """Decode and display base64-encoded chart images returned by the backend."""
    for fig_b64 in figures_b64:
        img_bytes = base64.b64decode(fig_b64)
        img = Image.open(io.BytesIO(img_bytes))
        st.image(img)


# --- Upload section ---
st.markdown('<div class="section-label"><span class="dot"></span>Upload your CSV</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"], label_visibility="collapsed")

if uploaded_file is not None and st.session_state.session_id is None:
    with st.spinner("Uploading and profiling dataset..."):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
        response = requests.post(f"{BACKEND_URL}/upload", files=files)

    if response.status_code == 200:
        data = response.json()
        st.session_state.session_id = data["session_id"]
        st.session_state.df_info = data["df_info"]
        st.success(f"Uploaded '{data['filename']}' — shape: {data['shape']}")
    else:
        st.error(f"Upload failed: {response.json().get('detail', 'Unknown error')}")

if uploaded_file is not None and st.button("Upload a different file"):
    st.session_state.session_id = None
    st.session_state.df_info = None
    st.rerun()

# --- EDA section ---
if st.session_state.session_id:
    st.markdown('<div class="section-label"><span class="dot"></span>Automated EDA</div>', unsafe_allow_html=True)
    if st.button("Run EDA"):
        with st.spinner("Generating and running analysis code (this may retry a few times)..."):
            response = requests.post(
                f"{BACKEND_URL}/eda",
                params={"session_id": st.session_state.session_id},
            )

        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                st.success(f"EDA complete (succeeded on attempt {result['attempts']})")
                if result["summary"]:
                    st.info(result["summary"])
                if result["stdout"]:
                    st.text(result["stdout"])
                show_figures(result["figures"])
            else:
                st.error(f"EDA failed after {result['attempts']} attempts")
                st.code(result["error"])
        else:
            st.error("Request failed.")

    # --- Q&A section ---
    st.markdown('<div class="section-label"><span class="dot"></span>Ask a question about your data</div>', unsafe_allow_html=True)
    question = st.text_input("e.g. 'What is the average value of column X?'", label_visibility="collapsed", placeholder="e.g. 'What is the average value of column X?'")
    if st.button("Ask") and question:
        with st.spinner("Thinking..."):
            response = requests.post(
                f"{BACKEND_URL}/query",
                json={"session_id": st.session_state.session_id, "question": question},
            )

        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                st.success(f"Answered (succeeded on attempt {result['attempts']})")
                if result["answer"] is not None:
                    st.write(result["answer"])
                if result["stdout"]:
                    st.text(result["stdout"])
                show_figures(result["figures"])
            else:
                st.error(f"Failed after {result['attempts']} attempts")
                st.code(result["error"])
        else:
            st.error("Request failed.")
else:
    st.info("Upload a CSV above to get started.")
