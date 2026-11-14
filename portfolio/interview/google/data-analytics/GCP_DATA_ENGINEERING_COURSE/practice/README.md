# BigQuery — Practice Suite

Seven hands-on modules on BigQuery, built to be **run**, not just read.

Every module follows the same anatomy as the course chapters, and every module has two kinds of
exercise:

- 💻 **Runs locally** — pure Python against the course's own modules in `../project/core/`. No
  account, no credentials, no bill. These run anywhere.
- 🌐 **Needs a BigQuery project** — GoogleSQL, `bq` commands and API calls. You need a project
  with billing enabled, and BigQuery API enabled on it.

**The split is the point.** Every concept in this suite has a part you can model on your laptop
and a part you can only verify against the real service. Do the local half first — it is where
the numbers come from, and the numbers are what you say in an interview.

---

## 📁 The modules

| # | Module | Covers | Time |
|---|---|---|---|
| 1 | [Storage Model](01-storage-model.md) | Serverless → Colossus → Capacitor → Dremel → Slots, storage/compute separation, columnar blocks, what BigQuery bills for, why BigQuery over PostgreSQL | 45 min |
| 2 | [Types of Storage](02-storage-types.md) | Standard tables, snapshots, clones, external and BigLake tables, logical vs materialized views, Iceberg/Delta/Hudi, the reference table DDL | 40 min |
| 3 | [Loading Data](03-loading-data.md) | Batch load jobs, Storage Write API (gRPC vs REST), at-least-once vs exactly-once, partial success, DTS, Datastream CDC, federated queries | 45 min |
| 4 | [Querying and Internals](04-querying-and-internals.md) | Scan → shuffle → aggregate → write, what happens inside one query, the broadcast join, skew, AutoMode | 50 min |
| 5 | [GoogleSQL](05-googlesql-language.md) | The type system, `NUMERIC` vs `FLOAT64`, `TIMESTAMP` vs `DATETIME`, arrays and structs, `UNNEST`, scripting and `RAISE EXCEPTION` | 55 min |
| 6 | [`bq` CLI and Scripting](06-bq-cli-and-scripting.md) | Every `bq` command and flag that matters, `.bigqueryrc`, dry runs, idempotent scripts, load → verify → assert | 45 min |
| 7 | [AI, ML and Agents](07-ai-ml-and-agents.md) | In-console assistance, AI/ML in SQL, `ML.GENERATE_TEXT`, embeddings and vector search, MCP servers, agent skills, agent analytics, IDE/terminal agents | 50 min |

Each module ends with:

- **🛠️ Common Errors and Fixes** — real error messages, and what actually caused them.
- **💡 Production Notes** — what a senior engineer would add, and why.
- **📚 Practice Exercises** — eight numbered exercises with no sub-bullets, because writing them
  out is the part that teaches you.

---

## 🗺️ How to run this

### The local half — no account needed

The course's core modules import nothing from Google Cloud. From this directory:

```bash
cd practice
python3 -c "
import sys
sys.path.insert(0, '../project/core')
from cost_model import estimate
print(estimate('bigquery', scanned_tb=10.0, apply_free_tier=False).total)
"
```

Expected output:

```text
62.5
```

That is the `$62.50` figure from the `interview/` bank, computed from the same price list.

The notebooks do this for you, with the path already set up:

```bash
cd practice
jupyter notebook notebooks/
```

Or execute them headless:

```bash
cd practice
jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb
```

### The cloud half — needs a project

You need a GCP project with billing enabled and the BigQuery API turned on.

```bash
# Authenticate and set the project for every later command.
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# Confirm BigQuery is reachable and billing is live.
bq ls --datasets=true --format=pretty
```

Then create the reference table that modules 2, 4 and 5 all use:

```sql
CREATE TABLE `retail.analytics.sales` (
    transaction_id STRING,
    store_id STRING,
    sale_date DATE,
    customer_id STRING,
    sales_amount NUMERIC
)
PARTITION BY sale_date
CLUSTER BY store_id;
```

> ⚠️ **Set a billing guardrail before you run anything.** BigQuery's first surprise bill is
> always a query nobody dry-ran. Run this once, then keep it:
>
> ```bash
> bq query --use_legacy_sql=false --dry_run --format=pretty \
>   'SELECT COUNT(*) FROM `YOUR_PROJECT_ID.YOUR_DATASET.sales`'
> ```
>
> And put a cap on every job: `--maximum_bytes_billed=10000000000`.

### The sample data — needs one command

The course's `sample_data/events.csv` and `malformed_events.csv` are generated, not committed.
If a module asks for them:

```bash
cd ..
python resources/sample_data.py --output-dir ./sample_data
```

The `.ndjson` files are committed and work as-is.

---

## 📓 The notebooks

| Notebook | What it does | Needs |
|---|---|---|
| [`01-storage-and-partitioning.ipynb`](notebooks/01-storage-and-partitioning.ipynb) | Partition decorators, byte math, the 100× win, idempotency keys | 💻 Local only |
| [`02-query-cost-lab.ipynb`](notebooks/02-query-cost-lab.ipynb) | The four architectures priced side by side, slot vs scan, storage tiers | 💻 Local only |
| [`03-bq-cli-lab.ipynb`](notebooks/03-bq-cli-lab.ipynb) | The `bq` command set, dry runs, the idempotent script pattern | 💻 Local + 📖 documented `bq` output |

The first two notebooks need nothing but Python. The third runs entirely locally too — its `bq`
sections are **documented** rather than executed, because `bq` is not installed everywhere and a
lab that claims to have run it when it did not is worse than no lab.

Two helper scripts live alongside the notebooks. Neither is a notebook — they are plain Python:

| Script | What it does |
|---|---|
| [`notebooks/_build_notebooks.py`](notebooks/_build_notebooks.py) | Regenerates all three `.ipynb` files from a single source of truth. Edit this, not the notebooks. |
| [`notebooks/_verify_notebooks.py`](notebooks/_verify_notebooks.py) | Executes every code cell in every notebook and reports failures with a traceback. |

```bash
cd practice
python3 notebooks/_build_notebooks.py     # rebuild
python3 notebooks/_verify_notebooks.py    # verify: "cells executed: 20   failures: 0"
```

---

## 🧭 A learning path

If you are preparing for the **certification**, work the modules in order. They follow the
course's Module 3 (BigQuery) and add the operational detail the exam assumes you have.

If you are preparing for an **interview**, do this:

1. **Module 1** — because "what is BigQuery and how does it work internally" is the opening
   question, and the S → C → C → D → S chain is the answer.
2. **Module 4** — because "how do you optimise a query" separates candidates.
3. **Module 5** — because the type-system questions (`NUMERIC` vs `FLOAT64`, `TIMESTAMP` vs
   `DATETIME`) are where most candidates are confidently wrong.
4. **Module 7** — because the AI and agent material is recent, and it is being asked about now.
5. Then re-read the other three for the details.

**Then answer every exercise out loud, without notes.** Reading a good answer and producing one
are different skills. If you cannot produce the first sentence of an answer from memory, you do
not know the question yet — that is the same standard the `interview/` bank sets, and it is the
one that holds up under follow-up questions.

### The three follow-ups that decide interviews

For every exercise, be ready to answer:

1. **"What would break in production?"** — the failure story.
2. **"What would you do instead?"** — the trade-off, with a reason.
3. **"Can you give me a number?"** — the concrete figure.

The exercises are written so that each one has a number attached. `$62.50 versus $0.62`.
`10,000 partitions`. `100 MB maximum row size`. `30 days retention`. `24 hours`. If you cannot
attach a number to an answer, that answer is not finished.

---

## ✅ Verification checklist

Work through this before you call the suite done:

| # | Check | How | Expected |
|---|---|---|---|
| 1 | The local modules import | `python3 -c "import sys; sys.path.insert(0,'../project/core'); import cost_model"` | No error |
| 2 | The cost model reproduces the headline figure | `estimate('bigquery', scanned_tb=10.0, apply_free_tier=False).total` | `62.5` |
| 3 | The four architectures price correctly | `compare_architectures()` | Streaming `0.0`, Spark `0.0`, partitioned `0.0625`, unpartitioned `6.25` |
| 4 | Partition decorators match BigQuery's convention | `partition_for_date('2026-01-15')` | `20260115` |
| 5 | The idempotency key is data-derived | `dedup_key('evt-0001', '20260115')` | `20260115:evt-0001` |
| 6 | The sample data is present | `python resources/sample_data.py --output-dir ./sample_data` | 4800 events, 12 malformed rows |
| 7 | The pipeline runs end to end | `python project/local_runner.py --run` | 4800 accepted, 12 rejected, 24 windows |
| 8 | The notebooks execute | `python3 notebooks/_verify_notebooks.py` | `cells executed: 20   failures: 0` |
| 9 | The notebooks also execute under Jupyter | `jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb` | All cells succeed |
| 10 | The tests still pass | `python3 -m pytest project/tests/ -q` | `102 passed` |
| 11 | Every "Expected output" block in the modules matches reality | `python3 _verify_modules.py` | `blocks checked: 12   mismatches: 0` |
| 12 | You can answer every question in 4 minutes | Re-read without notes | No hesitation on the first sentence |

Rows 6, 7 and 10 reach outside `practice/` into the course's own `resources/`, `project/` and
`project/tests/`. Rows 8 and 11 are self-contained: they check only this directory.

**What row 11 means.** Every `💻 Runs locally` code block in the seven modules is paired with a
verbatim `Expected output:` block. That block is not hand-written prose — it was produced by
running the code and pasting the result. [`_verify_modules.py`](_verify_modules.py) is what
keeps them honest:

```bash
cd practice
python3 _verify_modules.py
```

It extracts every `python` / `Expected output:` pair from the seven modules, executes the code,
and compares the result to the quoted block. A `mismatches: 0` means every number quoted in the
modules is one the code actually produced.

The `🌐 Needs a BigQuery project` blocks are **not** covered by this check — they require a GCP
project, and they are labelled as documented rather than executed.

---

## ⚠️ What is verified, and what is documented

This distinction matters, and it is the same one the course makes.

**Verified** — computed or executed here, and the output in the module is verbatim:

- Every local Python cell, and every number in a `💻 Runs locally` block.
- The cost figures, the byte counts, the 100× and 23× ratios.
- The API and type behaviour taken from the official BigQuery documentation.

**Documented** — correct as written, but requiring a GCP project to run:

- Every `bq` command and its output.
- Every BigQuery DDL statement.
- Every `ML.GENERATE_TEXT`, embedding and vector-search query.
- Error messages in "Common Errors and Fixes", which are quoted from BigQuery's documented
  behaviour rather than captured from a live session.

`bq` and `gcloud` are **not installed in the environment where this suite was written**, so no
`bq` command here has been executed. The flags, syntax and outputs come from the official
[BigQuery CLI reference](https://docs.cloud.google.com/bigquery/docs/reference/bq-cli-reference).
Run them yourself and compare.

---

## 🔗 Where this fits in the course

```text
GCP_DATA_ENGINEERING_COURSE/
├── chapters/          ← the teaching material (read this first)
├── interview/         ← 157 questions with model answers
├── notebooks/         ← the course's own notebooks
├── project/           ← the pure-Python core this suite exercises
├── resources/         ← setup guides, the sample-data generator, the linter
└── practice/          ← you are here
```

| If you want… | Go to |
|---|---|
| To learn the material | [`../chapters/13-bigquery-platform-overview.md`](../chapters/13-bigquery-platform-overview.md) |
| To be tested on it | [`../interview/03-analytics-and-cost.md`](../interview/03-analytics-and-cost.md) |
| To be tested on optimisation | [`../interview/07-query-optimization.md`](../interview/07-query-optimization.md) |
| To cram before an interview | [`../interview/top-40.md`](../interview/top-40.md) |
| To run the code | [`../project/README.md`](../project/README.md) |
| To practise it | **This directory** |

---

## 📖 Further Reading

- [BigQuery documentation home](https://docs.cloud.google.com/bigquery/docs)
- [BigQuery pricing](https://cloud.google.com/bigquery/pricing)
- [BigQuery quotas and limits](https://docs.cloud.google.com/bigquery/quotas)
- [Introduction to BigQuery AI](https://docs.cloud.google.com/bigquery/docs/ai-introduction)
- [Using the bq command-line tool](https://docs.cloud.google.com/bigquery/docs/bq-command-line-tool)
- [Google Cloud Architecture Center](https://cloud.google.com/architecture)
- [GCP Professional Data Engineer study guide](https://cloud.google.com/certification/resources/data-engineer-study-guide)
