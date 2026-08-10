"""
FastAPI backend for the Smart Data Analysis Platform.

Endpoints:
- POST /upload  -> upload a CSV, get back a session_id + df_info
- POST /eda     -> run automated EDA on the uploaded dataset
- POST /query   -> ask a natural language question about the dataset

Note: dataframes are kept in server memory keyed by session_id.
This is fine for a single-instance demo/prototype; it will NOT persist
across server restarts or scale across multiple server instances.
"""
import uuid
import base64
import io

from backend.services.profiling import get_df_info
from backend.services.executor import run_with_retry

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

from backend.services.profiling import get_df_info
from backend.services.executor import run_with_retry

app = FastAPI(title="Smart Data Analysis Platform API")

# Allow the Streamlit frontend (running on a different port/domain) to call this API.
# In production, restrict allow_origins to your actual Streamlit Cloud URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store: session_id -> {"df": DataFrame, "df_info": str}
SESSIONS: dict = {}

EDA_TASK = """Perform exploratory data analysis on df:
1. Print df.dtypes
2. Print df.isnull().sum()
3. Print df.describe() for numeric columns
4. Create a histogram for each numeric column (use subplots if there are multiple)
5. If there are categorical columns with few unique values, create a bar chart of value counts for up to 2 of them
Assign a short text summary (2-3 sentences) of key observations to a variable named `result`.
"""


class QueryRequest(BaseModel):
    session_id: str
    question: str


def figures_to_base64(figures: list) -> list:
    """Convert matplotlib figures to base64-encoded PNGs so they can be sent as JSON."""
    encoded = []
    for fig in figures:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        encoded.append(base64.b64encode(buf.read()).decode("utf-8"))
    return encoded


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Smart Data Analysis Platform API is running"}


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file, store it in memory, return a session_id + dataframe info."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    session_id = str(uuid.uuid4())
    df_info = get_df_info(df)
    SESSIONS[session_id] = {"df": df, "df_info": df_info}

    return {
        "session_id": session_id,
        "filename": file.filename,
        "shape": df.shape,
        "df_info": df_info,
    }


@app.post("/eda")
def run_eda(session_id: str):
    """Run automated EDA on a previously uploaded dataset."""
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Upload a CSV first.")

    df, df_info = session["df"], session["df_info"]
    exec_result = run_with_retry(EDA_TASK, df, df_info, max_retries=3)

    return {
        "success": exec_result["success"],
        "stdout": exec_result["stdout"],
        "summary": exec_result["result"],
        "figures": figures_to_base64(exec_result["figures"]),
        "attempts": exec_result["attempts"],
        "error": exec_result["error"] if not exec_result["success"] else None,
    }


@app.post("/query")
def ask_question(request: QueryRequest):
    """Answer a natural language question about a previously uploaded dataset."""
    session = SESSIONS.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Upload a CSV first.")

    df, df_info = session["df"], session["df_info"]
    task = f"{request.question}\nIf the answer is a number/text, assign it to `result` and print it. If it's better shown as a chart, create the chart."
    exec_result = run_with_retry(task, df, df_info, max_retries=3)

    return {
        "success": exec_result["success"],
        "stdout": exec_result["stdout"],
        "answer": exec_result["result"],
        "figures": figures_to_base64(exec_result["figures"]),
        "attempts": exec_result["attempts"],
        "error": exec_result["error"] if not exec_result["success"] else None,
    }