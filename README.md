# Smart Data Analysis Platform

**BetaBytez AI/ML Capstone — Task 5**
Umme Habiba Malik

An AI-powered data analysis tool: upload a CSV, get automated EDA, and ask questions about your data in plain English. A Groq-powered LLM generates pandas/matplotlib code on the fly, runs it in a sandboxed executor, and retries automatically if the generated code fails.

**Live app:** https://betabytez-aiml-task5-ummehabiba.streamlit.app
**Live API:** https://betabytez-aiml-task5-ummehabiba.onrender.com

> Note: the backend runs on Render's free tier, which spins down after inactivity. The first request after idle time can take 30–60 seconds to wake up.

---

## How it works

1. **Upload** a CSV — the backend profiles it (shape, dtypes, null counts, sample rows) and stores it in memory under a session ID.
2. **Auto-EDA** — a fixed task ("give me dtypes, nulls, describe(), and useful charts") is sent through the codegen engine.
3. **Ask a question** — your natural language question becomes the task instead.
4. Either way, the same engine handles it:
   - Groq LLM generates raw pandas/matplotlib code for the task
   - The code runs inside a restricted `exec()` sandbox (limited builtins, no file/network access)
   - If it errors, the error is fed back to the LLM and it retries (capped at 3 attempts)
   - If the question can't be answered from the available columns, the model is instructed to say so rather than guess

## Architecture

```
Streamlit (frontend)  --HTTP-->  FastAPI (backend)  --API-->  Groq LLM
                                       |
                                  exec() sandbox
                                  (pandas/matplotlib/seaborn)
```

**Backend** (`backend/`)
- `main.py` — FastAPI app: `/upload`, `/eda`, `/query` endpoints, in-memory session storage
- `services/profiling.py` — builds the dataframe summary fed into every LLM prompt
- `services/codegen.py` — Groq client + system prompt for code generation
- `services/executor.py` — sandboxed `exec()` + the generate → run → retry loop

**Frontend** (`frontend/`)
- `app.py` — Streamlit UI: file uploader, EDA display, Q&A chat box

**Notebooks** (`notebooks/`)
- `Task5_Day1_CoreEngine.ipynb` — the original Colab prototype, tested on the Titanic and Tips datasets before porting to FastAPI

## Tech stack

- **LLM:** Groq (`llama-3.1-8b-instant`)
- **Backend:** FastAPI, Uvicorn
- **Frontend:** Streamlit
- **Data:** pandas, matplotlib, seaborn
- **Hosting:** Render (backend), Streamlit Community Cloud (frontend)

## Running locally

**Backend**
```bash
pip install -r backend/requirements.txt
set GROQ_API_KEY=your_key_here      # Windows CMD
uvicorn backend.main:app --reload --port 8000
```

**Frontend** (in a separate terminal, with the backend running)
```bash
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

By default `frontend/app.py` points `BACKEND_URL` at the deployed Render URL — change it to `http://localhost:8000` if you want to test against a local backend instead.

## Known limitations

- Sessions are stored in server memory — they don't persist across backend restarts and won't scale across multiple server instances.
- Free-tier Render hosting means the backend sleeps after inactivity.
- The LLM occasionally needs a retry to produce runnable code; the retry loop handles this but doesn't guarantee success within the 3-attempt cap on very ambiguous requests.

## Testing evidence

The core engine was stress-tested in the Day 1 notebook across two datasets (Titanic, Tips) covering numeric, categorical, and null-heavy columns — both EDA and Q&A succeeded on the first attempt in all four runs. See `notebooks/Task5_Day1_CoreEngine.ipynb`, Section 8, for the logged results.
