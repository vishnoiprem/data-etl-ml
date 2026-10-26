"""
Build the FULL-LOOP notebook — a self-contained, runnable version
that walks through all 5 Meta L6 AI-Native DE interview rounds.

Each cell is loaded from full-loop/cells/ and bundled into one notebook.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CELLS_DIR = os.path.join(HERE, "cells")
OUT = os.path.join(HERE, "meta_l6_full_loop.ipynb")

# Load markdown cells
with open(os.path.join(CELLS_DIR, "md_cells.json")) as f:
    md_cells = json.load(f)

# Load code cells from .py files in order
code_files = sorted(f for f in os.listdir(CELLS_DIR) if f.startswith("cell_") and f.endswith(".py"))

md_by_id = {c["id"]: c for c in md_cells}

# Cell order: md interleaved with code, full 5-round walkthrough
cell_order = [
    ("header", "md"),
    ("round1_intro", "md"),
    ("round1_pitch", "md"),
    ("round1_ai_native_def", "md"),
    ("round1_why_team", "md"),
    ("round1_close", "md"),
    ("round2_intro", "md"),
    ("round2_modeling_q", "md"),
    ("code:cell_01_rag_schema.py", "code"),
    ("round2_modeling_close", "md"),
    ("round2_pipeline_q", "md"),
    ("code:cell_02_pipeline_demo.py", "code"),
    ("round2_pipeline_close", "md"),
    ("round2_sql_q", "md"),
    ("code:cell_03_sql_demo.py", "code"),
    ("round2_sql_close", "md"),
    ("round2_coding_q", "md"),
    ("code:cell_04_mmr.py", "code"),
    ("code:cell_05_rate_limiter.py", "code"),
    ("code:cell_06_cursor_paginate.py", "code"),
    ("round2_close", "md"),
    ("round3_intro", "md"),
    ("round3_pymk_q", "md"),
    ("code:cell_07_pymk.py", "code"),
    ("round3_pymk_close", "md"),
    ("round4_intro", "md"),
    ("round4_fullstack_q", "md"),
    ("code:cell_08_traces_ui.py", "code"),
    ("round4_close", "md"),
    ("round5_intro", "md"),
    ("round5_star1", "md"),
    ("round5_star2", "md"),
    ("round5_star3", "md"),
    ("round5_close", "md"),
    ("cheat_sheet", "md"),
    ("footer", "md"),
]

cells = []
for cell_id, cell_type in cell_order:
    if cell_type == "md":
        if cell_id not in md_by_id:
            print(f"WARNING: missing md cell {cell_id}")
            continue
        c = md_by_id[cell_id]
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": c["source"].splitlines(keepends=True)
        })
    else:
        fname = cell_id.split(":", 1)[1]
        fpath = os.path.join(CELLS_DIR, fname)
        if not os.path.exists(fpath):
            print(f"WARNING: missing code cell {fname}")
            continue
        with open(fpath) as f:
            src = f.read()
        cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": src.splitlines(keepends=True)
        })

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10"}
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

with open(OUT, "w") as f:
    json.dump(notebook, f, indent=1)

print(f"Notebook written: {OUT}")
print(f"Total cells: {len(cells)}")
print(f"Code cells: {sum(1 for c in cells if c['cell_type'] == 'code')}")
print(f"Markdown cells: {sum(1 for c in cells if c['cell_type'] == 'markdown')}")
