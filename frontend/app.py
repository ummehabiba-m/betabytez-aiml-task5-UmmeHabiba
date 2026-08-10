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
BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="Smart Data Analysis Platform", layout="wide")
st.title("📊 Smart Data Analysis Platform")
st.caption("Upload a CSV, get automated EDA, and ask questions in plain English.")

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
st.header("1. Upload your CSV")
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

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
    st.header("2. Automated EDA")
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
    st.header("3. Ask a question about your data")
    question = st.text_input("e.g. 'What is the average value of column X?'")
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