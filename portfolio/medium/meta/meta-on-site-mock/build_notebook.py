# Build the notebook from cells/ folder
# Usage: python3 build_notebook.py
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CELLS_DIR = os.path.join(HERE, "cells")
OUT = os.path.join(HERE, "meta_l6_onsite_mock.ipynb")

# Load markdown cells
with open(os.path.join(CELLS_DIR, "md_cells.json")) as f:
    md_cells = json.load(f)

# Load code cells from .py files in order
code_files = sorted(f for f in os.listdir(CELLS_DIR) if f.startswith("cell_") and f.endswith(".py"))

# Build the ordered cell list
cells = []

# Build an id -> md cell lookup
md_by_id = {c["id"]: c for c in md_cells}

# Define the cell order: (id, type) - use None for code cells that are loaded from files
cell_order = [
    ("header", "md"),
    ("round2_q1_intro", "md"),
    ("round2_q1_schema", "md"),  # this one has source as code
    ("round2_q1_talking_points", "md"),
    ("round2_q2_intro", "md"),
    ("round2_q2_talking_points", "md"),
    ("round2_q3_intro", "md"),
    ("code:cell_01_mmr.py", "code"),
    ("code:cell_02_mmr_dedup.py", "code"),
    ("round2_q3_talking_points", "md"),
    ("round2_q4_intro", "md"),
    ("code:cell_03_sql_seed.py", "code"),
    ("code:cell_04_sql_eval.py", "code"),
    ("code:cell_05_sql_ab.py", "code"),
    ("code:cell_06_sql_gold.py", "code"),
    ("round3_intro", "md"),
    ("round3_talking_points", "md"),
    ("round4_intro", "md"),
    ("round4_talking_points", "md"),
    ("round5_intro", "md"),
    ("vector_db_intro", "md"),
    ("code:cell_07_vector_db.py", "code"),
    ("benchmark_intro", "md"),
    ("code:cell_08_benchmark.py", "code"),
    ("hybrid_intro", "md"),
    ("code:cell_09_hybrid.py", "code"),
    ("drift_intro", "md"),
    ("code:cell_10_drift.py", "code"),
    ("reranker_intro", "md"),
    ("code:cell_11_reranker.py", "code"),
    ("streaming_intro", "md"),
    ("code:cell_12_streaming.py", "code"),
    ("timeseries_intro", "md"),
    ("code:cell_13_timeseries.py", "code"),
    ("migration_intro", "md"),
    ("code:cell_14_migration.py", "code"),
    ("tracing_intro", "md"),
    ("code:cell_15_opentelemetry.py", "code"),
    ("cost_intro", "md"),
    ("code:cell_16_cost_calculator.py", "code"),
    ("pymk_intro", "md"),
    ("code:cell_17_pymk.py", "code"),
    ("mmr_vs_rerank_intro", "md"),
    ("code:cell_18_mmr_vs_rerank.py", "code"),
    ("bm25_intro", "md"),
    ("code:cell_19_bm25_deepdive.py", "code"),
    ("kafka_intro", "md"),
    ("code:cell_20_kafka_delivery.py", "code"),
    ("hnsw_intro", "md"),
    ("code:cell_21_hnsw.py", "code"),
    ("eval_intro", "md"),
    ("code:cell_22_eval_metrics.py", "code"),
    ("clickhouse_intro", "md"),
    ("code:cell_23_clickhouse.py", "code"),
    ("spark_intro", "md"),
    ("code:cell_24_spark_backfill.py", "code"),
    ("gdpr_intro", "md"),
    ("code:cell_25_gdpr.py", "code"),
    ("query_optimizer_intro", "md"),
    ("code:cell_26_query_optimizer.py", "code"),
    ("finetune_intro", "md"),
    ("code:cell_27_embedding_finetune.py", "code"),
    ("async_ingestion_intro", "md"),
    ("code:cell_28_async_batch_ingestion.py", "code"),
    ("chunking_intro", "md"),
    ("code:cell_29_chunking_strategies.py", "code"),
    ("multitenancy_intro", "md"),
    ("code:cell_30_multitenancy.py", "code"),
    ("ai_native_intro", "md"),
    ("code:cell_31_ai_native_eval_loop.py", "code"),
    ("footer", "md"),
]

for cell_id, cell_type in cell_order:
    if cell_type == "md":
        if cell_id not in md_by_id:
            print(f"WARNING: missing md cell {cell_id}")
            continue
        c = md_by_id[cell_id]
        if c["type"] != "markdown":
            # The schema one is actually a code cell in md_cells.json
            cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": c["source"].splitlines(keepends=True)
            })
        else:
            cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": c["source"].splitlines(keepends=True)
            })
    elif cell_type == "code":
        # cell_id is "code:filename.py"
        fname = cell_id.split(":", 1)[1]
        fpath = os.path.join(CELLS_DIR, fname)
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
