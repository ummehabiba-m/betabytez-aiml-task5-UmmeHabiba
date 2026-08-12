"""
Code generation agent.
Takes a task description + dataframe context, asks Groq to generate
raw executable Python code (pandas/matplotlib/seaborn) — no explanations,
no markdown fences, so it can be passed straight to exec().
"""
import os
from groq import Groq

# API key is read from an environment variable, never hardcoded.
# Set GROQ_API_KEY in your terminal/.env before running the backend.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

MODEL_NAME = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are a Python data analysis code generator.

Rules:
- You will be given info about a pandas DataFrame called `df` (already loaded, do not reload or recreate it).
- First, check whether the task is actually answerable using the columns available in `df`. If the task is unclear, nonsensical, unrelated to the data, or cannot be answered with the given columns, do NOT guess or default to an unrelated calculation. Instead, write code that sets:
  result = "I cannot answer this question based on the given data."
  and print(result), then stop — do not attempt any other computation.
- If the task IS answerable, write Python code that accomplishes it using `df`.
- Use pandas, matplotlib.pyplot (as plt), and seaborn (as sns) — all already imported.
- If creating a chart, call plt.show() at the end of that chart's code.
- If the task expects a text/numeric result, assign it to a variable named `result` and print it.
- Return ONLY raw Python code. No markdown fences (no ```), no explanations, no comments about what you're doing outside the code.
- Keep code safe: no file I/O, no network calls, no imports beyond what's already available.
"""

def generate_code(task_description: str, df_info: str, error_context: str = None) -> str:
    """
    Call Groq to generate pandas/matplotlib code for a given task.

    If error_context is provided, this is a retry — the previous code's
    error is included so the LLM can fix its mistake instead of guessing blind.
    """
    user_prompt = f"""DataFrame info:
{df_info}

Task: {task_description}
"""

    if error_context:
        user_prompt += f"""
IMPORTANT: Your previous attempt failed with this error:
{error_context}

Fix the code so it runs without error. Return the corrected code only.
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    code = response.choices[0].message.content.strip()

    # Safety net: strip markdown fences if the model adds them anyway
    if code.startswith("```"):
        code = code.strip("`")
        if code.startswith("python"):
            code = code[len("python"):]
    return code.strip()