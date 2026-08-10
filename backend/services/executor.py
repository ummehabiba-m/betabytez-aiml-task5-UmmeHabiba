"""
Execution engine.
safe_exec() runs LLM-generated code in a restricted namespace.
run_with_retry() ties codegen + execution together, retrying on
failure by feeding the error back to the LLM.
"""
import io
import contextlib
import traceback
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend, needed for server-side chart generation
import matplotlib.pyplot as plt
import seaborn as sns

from .codegen import generate_code


def safe_exec(code: str, df: pd.DataFrame) -> dict:
    """
    Execute LLM-generated code in a restricted namespace.

    Returns a dict with:
      - success: bool
      - stdout: captured print() output
      - result: value of `result` variable, if set by the code
      - figures: list of matplotlib figures created during execution
      - error: traceback string, if execution failed
    """
    safe_globals = {
        "__builtins__": {
            "print": print, "len": len, "range": range, "str": str, "int": int,
            "float": float, "list": list, "dict": dict, "set": set, "tuple": tuple,
            "sum": sum, "min": min, "max": max, "sorted": sorted, "enumerate": enumerate,
            "zip": zip, "round": round, "abs": abs, "bool": bool,
            "__import__": __import__,
        },
        "pd": pd,
        "plt": plt,
        "sns": sns,
        "df": df,
    }
    local_vars = {}
    stdout_capture = io.StringIO()

    plt.close("all")

    try:
        with contextlib.redirect_stdout(stdout_capture):
            exec(code, safe_globals, local_vars)

        figures = [plt.figure(n) for n in plt.get_fignums()]

        return {
            "success": True,
            "stdout": stdout_capture.getvalue(),
            "result": local_vars.get("result"),
            "figures": figures,
            "error": None,
        }
    except Exception:
        return {
            "success": False,
            "stdout": stdout_capture.getvalue(),
            "result": None,
            "figures": [],
            "error": traceback.format_exc(),
        }


def run_with_retry(task_description: str, df: pd.DataFrame, df_info: str, max_retries: int = 3) -> dict:
    """
    Generate + execute code for a task, retrying on failure.
    Each retry feeds the previous error back to the LLM so it can self-correct.
    """
    error_context = None
    last_code = None
    last_exec_result = None

    for attempt in range(1, max_retries + 1):
        code = generate_code(task_description, df_info, error_context)
        last_code = code

        exec_result = safe_exec(code, df)
        last_exec_result = exec_result

        if exec_result["success"]:
            exec_result["attempts"] = attempt
            exec_result["final_code"] = code
            return exec_result

        error_context = exec_result["error"]

    last_exec_result["attempts"] = max_retries
    last_exec_result["final_code"] = last_code
    return last_exec_result