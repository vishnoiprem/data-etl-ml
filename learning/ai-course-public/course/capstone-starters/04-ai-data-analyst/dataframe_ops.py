"""
DataFrame Ops - Schema inference + pandas code generation
=========================================================
- infer_schema: read a CSV, return column types + sample values
- generate_pandas_code: ask GPT-4o to write pandas code for a question
"""

import os
import time
import json
import logging
import pandas as pd
from openai import OpenAI

logger = logging.getLogger("data-analyst.df")

CODE_MODEL = "gpt-4o"
PRICING = {"gpt-4o": {"input": 2.50, "output": 10.00}}

SAMPLE_ROWS = 3
MAX_SAMPLE_CHARS = 60
MAX_COLUMNS = 100


def infer_schema(csv_path: str) -> tuple[list[dict], int, int]:
    """Read a CSV, return (schema, n_rows, n_cols)."""
    df = pd.read_csv(csv_path)
    if df.shape[1] > MAX_COLUMNS:
        raise ValueError(f"Too many columns: {df.shape[1]} (max {MAX_COLUMNS})")
    schema = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        samples = df[col].head(SAMPLE_ROWS).tolist()
        samples = [str(s)[:MAX_SAMPLE_CHARS] for s in samples]
        nulls = int(df[col].isna().sum())
        schema.append({
            "name": str(col),
            "dtype": dtype,
            "samples": samples,
            "nulls": nulls,
        })
    return schema, int(df.shape[0]), int(df.shape[1])


def generate_pandas_code(
    question: str,
    schema: list[dict],
    csv_path: str,
    openai_api_key: str,
) -> tuple[str, float]:
    """Ask GPT-4o to write pandas code that answers `question`."""
    client = OpenAI(api_key=openai_api_key)

    schema_str = "\n".join(
        f"- {c['name']} ({c['dtype']}, {c['nulls']} nulls) — examples: {c['samples']}"
        for c in schema
    )

    sys = (
        "You are a data analyst. Given a CSV schema and a question, write pandas code that answers the question.\n"
        "The DataFrame is already loaded as `df` (CSV at the given path).\n"
        "Assign your final answer to a variable called `result`.\n"
        "Use only pandas and numpy. No other libraries.\n"
        "Be concise — prefer 1-3 lines of code.\n"
        "If the question is ambiguous, pick the most reasonable interpretation.\n"
        "Return JSON: {\"code\": \"<python>\", \"explanation\": \"<1 sentence>\"}"
    )
    user = (
        f"CSV path: {csv_path}\n\n"
        f"Schema:\n{schema_str}\n\n"
        f"Question: {question}\n\n"
        f"Write the pandas code:"
    )

    start = time.time()
    resp = client.chat.completions.create(
        model=CODE_MODEL,
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    elapsed = time.time() - start
    usage = resp.usage
    cost = (usage.prompt_tokens / 1e6) * PRICING[CODE_MODEL]["input"] + \
           (usage.completion_tokens / 1e6) * PRICING[CODE_MODEL]["output"]

    parsed = json.loads(resp.choices[0].message.content)
    code = parsed["code"].strip()
    if code.startswith("```python"):
        code = code.split("```python", 1)[1].split("```", 1)[0].strip()
    elif code.startswith("```"):
        code = code.split("```", 1)[1].split("```", 1)[0].strip()

    logger.info(f"code gen {elapsed:.1f}s in_tok={usage.prompt_tokens} out_tok={usage.completion_tokens} cost=${cost:.4f}")
    return code, cost
