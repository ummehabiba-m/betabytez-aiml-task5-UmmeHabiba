"""
Dataframe profiling utilities.
Builds a compact text summary of a dataframe to feed into LLM prompts,
so the model has enough context to write correct pandas code without
us sending the entire dataset.
"""
import io
import pandas as pd


def get_df_info(df: pd.DataFrame) -> str:
    """
    Returns a text summary of the dataframe: shape, dtypes, null counts,
    and a small sample of rows.
    """
    buffer = io.StringIO()
    df.info(buf=buffer)
    info_str = buffer.getvalue()

    null_counts = df.isnull().sum()
    nulls_str = (
        null_counts[null_counts > 0].to_string()
        if null_counts.sum() > 0
        else "No missing values"
    )

    summary = f"""
Shape: {df.shape[0]} rows, {df.shape[1]} columns

Column info:
{info_str}

Null counts (columns with nulls only):
{nulls_str}

Sample rows:
{df.head(3).to_string()}
"""
    return summary.strip()