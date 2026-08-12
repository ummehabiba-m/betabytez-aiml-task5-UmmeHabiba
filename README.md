# Smart Data Analysis Platform

**BetaBytez AI/ML Capstone — Task 5**
By Umme Habiba Malik

## What this project does

You upload a CSV file. The app then:

1. Automatically looks at your data and gives you a summary — column types, missing values, basic statistics, and a few charts. This is called **EDA (Exploratory Data Analysis)**, and normally a person would write code by hand to do this. Here, an AI does it for you.
2. Lets you **ask questions about your data in plain English** — like "which day has the highest sales?" — and get a real answer, calculated from your actual data, not a guess.

Behind the scenes, an AI model (Groq) writes Python code to answer your question, runs that code safely, and checks if it worked. If the code has an error, the AI automatically tries again with the error message so it can fix its own mistake — up to 3 tries.

**Live app (frontend):** https://betabytez-aiml-task5-ummehabiba1.streamlit.app/
**Live API (backend):** https://betabytez-aiml-task5-ummehabiba.onrender.com

> Note: The backend is hosted on a free plan that "sleeps" when nobody uses it for a while. The first request after it's been idle can take 30–60 seconds to wake up. This is normal — just wait.

---

## How it works, step by step

1. **You upload a CSV** in the Streamlit app.
2. The **backend** (FastAPI) receives it, reads it into a pandas DataFrame, and creates a short text summary of it (column names, types, number of missing values, a few sample rows). This summary is saved under a unique session ID so the app remembers your file while you keep using it.
3. When you click **"Run EDA"** or type a **question**, that request (plus the data summary from step 2) gets sent to the Groq AI model.
4. The AI model **writes Python code** that would answer the request — for example, code that calculates an average or draws a bar chart.
5. That code is **run inside a sandbox** — a restricted, safe environment that can only use pandas/matplotlib/seaborn and cannot access files, the internet, or anything else on the server. This stops the AI from accidentally (or intentionally) doing anything harmful.
6. **If the code fails** (for example, a typo or wrong column name), the error message is sent back to the AI, and it tries writing the code again. This happens automatically, up to 3 times.
7. **If the question genuinely can't be answered** from the uploaded data, the AI is instructed to say so honestly instead of making up an answer.
8. The final result (text, numbers, or a chart) is sent back and displayed in the Streamlit app.

## Why it's built this way (the architecture)

```
 You (browser)
      |
      v
Streamlit app (frontend)  --- sends your file/question over the internet --->  FastAPI (backend)
      ^                                                                              |
      |                                                                              v
 shows you the result                                                    Groq AI model writes code
                                                                                       |
                                                                                       v
                                                                          Code runs in a safe sandbox
                                                                          (retries automatically on error)
```

The **frontend** (Streamlit) and **backend** (FastAPI) are two completely separate programs that talk to each other over the internet, using two different hosting services:

- **Frontend** is hosted on **Streamlit Community Cloud** — this is just the visual webpage you interact with.
- **Backend** is hosted on **Render** — this does all the actual work (reading the CSV, calling the AI, running code).

They're kept separate on purpose: it's a common real-world pattern where the "what the user sees" part and the "the actual logic" part are built and deployed independently.

---

## Full project structure

```
betabytez-aiml-task5-UmmeHabiba/
│
├── README.md                    <- you are here
├── .gitignore                   <- tells Git which files to ignore (secrets, cache files, etc.)
│
├── notebooks/
│   └── Task5_Day1_CoreEngine.ipynb
│       ^ The very first prototype, built and tested in Google Colab.
│         This is where the AI code-generation + retry logic was first
│         built and proven to work, before being copied into the
│         proper backend/frontend files below. Kept as a record of
│         the testing process (see Section 8 in the notebook for
│         test results on 2 sample datasets).
│
├── backend/                     <- the FastAPI server (the "engine room")
│   ├── main.py
│   │     ^ The actual API. Defines what happens when someone:
│   │       - uploads a file       (POST /upload)
│   │       - asks for EDA          (POST /eda)
│   │       - asks a question       (POST /query)
│   │       Also handles CORS (letting the frontend talk to it) and
│   │       stores each user's uploaded data temporarily in memory.
│   │
│   ├── requirements.txt
│   │     ^ List of Python packages the backend needs installed
│   │       (FastAPI, pandas, Groq's library, etc.)
│   │
│   ├── pyproject.toml
│   │     ^ Configuration file used during deployment to tell the
│   │       hosting service how to install and run this project.
│   │
│   └── services/                <- the actual "brains" of the app, split into pieces
│       ├── __init__.py
│       │     ^ An empty file that tells Python "this folder is a package"
│       │       so the files inside it can import each other properly.
│       │
│       ├── profiling.py
│       │     ^ Function: get_df_info(df)
│       │       Takes your uploaded data and turns it into a short text
│       │       summary (column types, missing values, sample rows).
│       │       This summary is what gets shown to the AI so it
│       │       understands your data without needing the whole file.
│       │
│       ├── codegen.py
│       │     ^ Function: generate_code(...)
│       │       Talks to the Groq AI model. Sends it your question +
│       │       the data summary, and gets back Python code as text.
│       │       Contains the exact instructions ("system prompt") that
│       │       tell the AI how to behave — e.g. "only return code, no
│       │       explanations" and "if you can't answer, say so honestly."
│       │
│       └── executor.py
│             ^ Functions: safe_exec(...) and run_with_retry(...)
│               safe_exec = actually runs the AI's code in a locked-down
│               environment and captures the output (text, numbers, or
│               charts), or catches the error if it fails.
│               run_with_retry = the loop that ties it together:
│               generate code → run it → if it fails, try again with
│               the error message → up to 3 attempts.
│
├── frontend/                    <- the Streamlit app (what you actually see/click)
│   ├── app.py
│   │     ^ The whole visual interface: the upload box, the "Run EDA"
│   │       button, the question box, and the styling (colors, fonts,
│   │       layout). This file sends your actions to the backend and
│   │       displays whatever comes back.
│   │
│   └── requirements.txt
│         ^ List of Python packages the frontend needs (Streamlit,
│           requests, Pillow for images).
│
└── docs/
    └── screenshots/
          ^ Image files showing the app actually working — used as
            proof/demo material in this README and for grading.
```

**Note on the root `requirements.txt`:** an early empty version of this file caused a deployment bug (the hosting service was reading it instead of `backend/requirements.txt`, and finding nothing in it). It was deleted from the repo root — each of `backend/` and `frontend/` has its own `requirements.txt` instead, which is enough.

---

## Tech stack (what's used and why)

| Tool | What it's for |
|---|---|
| **Groq** (`llama-3.1-8b-instant`) | The AI model that writes the Python analysis code. Groq is fast and free-tier friendly, which matters for quick retries. |
| **FastAPI** | The backend framework — handles requests from the frontend, runs the AI + code engine. |
| **Uvicorn** | The actual server software that runs the FastAPI app. |
| **Streamlit** | The frontend framework — turns Python into a clickable webpage without needing HTML/CSS/JavaScript from scratch (though custom CSS was added for the theme). |
| **pandas** | Reads and analyzes the CSV data. |
| **matplotlib / seaborn** | Draw the charts. |
| **Render** | Hosts the backend (FastAPI) so it's live on the internet. |
| **Streamlit Community Cloud** | Hosts the frontend so anyone can open the app in a browser. |

---

## Running it on your own computer

You need two terminals open at the same time — one for the backend, one for the frontend.

**Terminal 1 — Backend**
```bash
pip install -r backend/requirements.txt
set GROQ_API_KEY=your_groq_key_here
uvicorn backend.main:app --reload --port 8000
```
Leave this running. It should say `Uvicorn running on http://127.0.0.1:8000`.

**Terminal 2 — Frontend**
```bash
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```
This opens the app in your browser automatically, usually at `http://localhost:8501`.

By default, `frontend/app.py` is set to talk to the live Render backend (`BACKEND_URL`). If you want it to talk to your own local backend instead, change that line to:
```python
BACKEND_URL = "http://localhost:8000"
```

---

## Things this project does NOT do (known limitations)

Being upfront about these matters for grading and for anyone reading this later:

- **No permanent storage.** Uploaded data is kept only in the server's memory while it's running. If the backend restarts, everyone's uploaded files are gone. This is fine for a demo/capstone, not fine for a real product.
- **Single-server only.** It's not built to run across multiple servers at once (no shared database for sessions).
- **Free hosting means slow wake-ups.** The Render backend sleeps after ~15 minutes of no traffic and takes up to a minute to wake back up.
- **The AI isn't perfect.** It usually gets the code right in 1 try, sometimes needs the retry loop, and very rarely fails all 3 tries on a confusing question — in which case it will show an error rather than crash.

---

## Testing done

The core engine (before it became the FastAPI backend) was tested inside `notebooks/Task5_Day1_CoreEngine.ipynb` using two real datasets:

- **Titanic** (has missing values, mixed data types — a realistic messy dataset)
- **Tips** (a different structure, used to prove the engine isn't hardcoded to one dataset)

Both **EDA** and **question-answering** succeeded on the very first attempt for both datasets (4 out of 4 test runs passed). Full results are logged in Section 8 of that notebook.
