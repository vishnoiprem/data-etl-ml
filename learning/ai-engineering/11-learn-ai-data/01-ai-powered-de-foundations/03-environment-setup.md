# Lesson 3 — Environment Setup

> **Type:** Article · **Length:** 7 min read · **Level:** Beginner
> **Author:** Gorijala Kiran · **52 completed** · **5.0 (2)**
> **Source:** [Data Vidhya — AI for Data Engineering](https://datavidhya.com/learn/ai-for-data-engineering/)

---

## The difference between "AI was meh" and "AI doubled my output" is setup

IDE configuration, context files, schema awareness, and a setup guide that actually works.

I have watched dozens of data engineers try an AI coding assistant for the first time. About half of them come back a week later and say, *"Honestly, it was kind of meh. It writes okay SQL, but I spend more time fixing it than writing it myself."* The other half come back and say, *"I am shipping at twice my old speed. I don't want to go back."*

Same tools. Same job. Wildly different results.

**The difference is almost never the model.** GPT-4, Claude, and the latest Copilot model are all good enough to write production data engineering code. The difference is **setup**. Your IDE configuration, your context files, your schema exposure, and your project structure decide whether the AI generates useful code or plausible-sounding garbage. If you skip the setup, you are giving the AI a blindfold and asking it to draw your house. Of course the result is bad.

This article is the setup guide I wish someone had given me when I started using AI tools for pipeline work. We will pick a default assistant, configure your IDE with a real rules file you can copy today, wire AI into your SQL and Spark workflows, and avoid the four setup mistakes that make people give up before the tools have a chance to help.

---

## Key Insight

> AI coding tools are downstream of **context**. The model is fixed. The only lever you control is how much relevant context the AI sees when you ask it a question. **Setup is the practice of making that context easy to provide on every prompt, without you thinking about it.**

```
                    AI QUALITY IS DOWNSTREAM OF CONTEXT

   ┌──────────────────────────────────────────────────────────┐
   │  FIVE SOURCES FEED THE AI:                               │
   │  ───────────────────────                                 │
   │   1. Rules file (CLAUDE.md / .cursorrules)               │
   │   2. Schema docs (schema.md, dbt manifest)                │
   │   3. Type hints + docstrings                             │
   │   4. Canonical templates (DAG, dbt, Spark session)       │
   │   5. Pinned lockfile (pyproject.toml, uv.lock)            │
   └──────────────────────────────────────────────────────────┘
                           │
                           ▼
                        ┌──────┐
                        │  AI  │
                        └──────┘
                           │
                           ▼
              informed output (90% production-ready)
                          vs
              plausible garbage (without context)
```

---

## Choosing Your AI Coding Assistant

There are **five families worth your time in 2026**: GitHub Copilot, Cursor, Claude Code, OpenAI Codex (the ChatGPT cloud agent and the open-source Codex CLI), and Amazon Q Developer. Most "AI coding tool" reviews you'll find online are either wrappers around one of these or marketing posts for a smaller product. Don't get lost in the long tail.

Here is the honest comparison:

| Tool | Best at | Weak at | Cost | Start here if... |
|---|---|---|---|---|
| **Cursor** | Multi-file edits, refactoring, project-wide context, pipeline development | Some friction if your team is on JetBrains | $20/mo Pro | You do heavy pipeline work and live in VS Code |
| **Claude Code** | Complex reasoning, terminal-native workflows, long-context tasks, agentic coding | No inline tab completion, learning curve | $20/mo (or API usage) | You like a terminal and want the strongest reasoning |
| **GitHub Copilot** | Inline completions, broadest IDE support, frictionless team rollout | Weaker at multi-file changes, less context-aware | $10–19/mo | Your team is already on it, or you live in JetBrains |
| **OpenAI Codex / Codex CLI** | Cloud-delegated tasks inside ChatGPT, async background work, parallel PRs, terminal scripting | Less interactive than Cursor or Claude Code for live edits | Included in ChatGPT Plus/Pro; CLI is free + API | You already pay for ChatGPT and want a coding agent that can run tasks in the background |
| **Amazon Q Developer** | AWS-native workflows (Glue, Athena, Redshift), free tier | Less mature outside AWS | Free tier + paid | You are deep in AWS data services |

**The opinionated default:** Start with **Cursor** or **Claude Code** if you do heavy pipeline development. Cursor wins on day-one productivity because the inline experience is excellent. Claude Code wins on hard problems because the reasoning is a notch higher and it handles long contexts (whole repos, large log files) without falling apart. I personally use both. Cursor for fast SQL and dbt work, Claude Code for architectural changes and debugging.

If your team is already standardized on Copilot, just use Copilot. The marginal gain from switching is real but small. **Tool drama is not worth the tax of being out of sync with your team.**

If you already pay for ChatGPT Plus or Pro, OpenAI Codex is free in your sub. The killer use case is async tasks: ask it to *"fix the failing dbt tests on this branch"* or *"write the Airflow DAG for the new ingestion source,"* then check back in 15 minutes. Codex CLI plays the same role in your terminal if you'd rather pay per-token via the OpenAI API.

**Don't agonize over this choice.** Pick one, use it seriously for a week (not for an hour), and switch if it doesn't click. The patterns transfer. What you learn about prompting and context applies to all of them.

```
       DECISION FLOWCHART
       ──────────────────

              ┌─────────────────────────┐
              │  Is your team on        │
              │  Copilot already?       │─── YES ──► Use Copilot
              └────────────┬────────────┘
                           │ NO
                           ▼
              ┌─────────────────────────┐
              │  Do you pay for         │
              │  ChatGPT Plus/Pro?      │─── YES ──► Use Codex
              └────────────┬────────────┘
                           │ NO
                           ▼
              ┌─────────────────────────┐
              │  Deep in AWS data       │
              │  stack (Glue/Athena)?   │─── YES ──► Use Amazon Q
              └────────────┬────────────┘
                           │ NO
                           ▼
              ┌─────────────────────────┐
              │  Heavy pipelines in     │
              │  VS Code?               │─── YES ──► Cursor
              └────────────┬────────────┘
                           │ NO
                           ▼
                  Default: Claude Code

       ─────────────────────────────────────────
       Commit to one tool for 30 days. Don't tool-hop.
```

### A second tier worth watching
These are not the default I'd recommend to a DE who just wants to ship this quarter, but they are moving fast and a few of them could be in the top tier by next year:

- **Windsurf (formerly Codeium)** has the strongest "agentic IDE" experience and a free tier with surprising power. If you don't want to pay anything, start here.
- **Google Jules** is Google's autonomous coding agent. Strong if you live inside Google Cloud and Gemini's model fits your work.
- **Gemini Code Assist** is the IDE-extension equivalent. Reasonable on BigQuery and GCP-heavy stacks.
- **Devin (Cognition)** is the most aggressive bet on fully autonomous coding. Pricey, useful for well-scoped greenfield tasks, less useful for the messy debugging that fills a DE's week.
- **Aider** is the open-source terminal coder. Pick it if you want zero vendor lock-in and full transparency over what's being sent to a model.

For a DE in 2026, the calculus is simple: **pick one of the top five, configure it well, and stop reading "which AI tool is best" blog posts.** The configuration matters more than the choice.

> ⚠️ **Don't tool-hop.** The biggest waste of time I see in this space is people switching tools every few days, never giving any of them a chance to learn their codebase or for the user to learn the tool's quirks. **Commit to one for at least 30 days.** Then evaluate.

---

## IDE Configuration for Maximum Effectiveness

This is the highest-value section in the article. **The single biggest lever you have is the rules file:** a small Markdown file that tells your AI assistant about your stack, your conventions, your data model, and your preferences. Cursor calls it `.cursorrules` (or the newer `.cursor/rules/*.mdc`). Claude Code uses `CLAUDE.md`. Same idea.

**Without a rules file, the AI starts from zero on every prompt.** It guesses your dialect, invents column names, picks materialization strategies at random, and gives you generic answers. **With a rules file, it answers like a teammate who has been on your project for six months.**

Here is a real `CLAUDE.md` you can drop into a data engineering repo today and adapt:

```markdown
# Data Platform Engineering Rules

## Stack
- Warehouse: Snowflake (account: acme-prod). Default warehouse: TRANSFORM_WH.
- Transformation: dbt-snowflake 1.8+. Models live in `models/`. Macros in `macros/`.
- Orchestration: Airflow 2.9, MWAA. DAGs in `dags/`. One DAG per source domain.
- Python: 3.11. Use `uv` for env management. Type hints required for all functions.
- Spark jobs: PySpark 3.5 on Databricks. Cluster configs in `infra/clusters/`.

## SQL conventions
- Dialect: Snowflake SQL. Never write generic ANSI SQL.
- Always use CTEs, never nested subqueries. One CTE per logical step.
- snake_case for everything. Tables plural, columns singular.
- Date columns end in `_at` (UTC timestamps) or `_date` (DATE type).
- Always handle NULL explicitly. `WHERE x != 'foo'` excludes NULLs; use `COALESCE` or `IS NOT NULL`.
- For incremental models, use `unique_key` and `merge` strategy by default.

## dbt conventions
- Three layers: `staging/` (1:1 with sources), `intermediate/` (joins, business logic),
  `marts/` (final tables).
- Staging models: views. Intermediate: ephemeral or view. Marts: tables or incremental.
- Every mart model must have: `unique` and `not_null` tests on the primary key,
  a `description`, and column-level descriptions.
- Sources defined in `models/staging/<source>/_sources.yml`.

## Python conventions
- Use Pydantic v2 for data validation.
- Use `pandas` only for files under 1GB. For anything larger, default to PySpark or DuckDB.
- All pipeline scripts must be idempotent. Re-running the same script with the same
  input must produce the same output.
- Logging: `structlog`, JSON output, level set via `LOG_LEVEL` env var.

## What to never do
- Never write `SELECT *` in production models.
- Never use Python UDFs in Spark when a native function exists.
- Never `.collect()` a DataFrame without checking row count first.
- Never commit credentials or `.env` files. Secrets live in AWS Secrets Manager.
- Never modify production data without an explicit `is_prod=True` flag in the script.

## Schema context
- Core fact tables: `marts.fct_orders`, `marts.fct_events`, `marts.fct_payments`.
- Core dimensions: `marts.dim_customers`, `marts.dim_products`, `marts.dim_dates`.
- Refer to `docs/data-model.md` for full schema.
```

```
   ANATOMY OF A GREAT RULES FILE
   ─────────────────────────────
   1. Stack         (lead with this — warehouse, framework, versions, dialect)
   2. SQL conventions
   3. dbt conventions
   4. Python conventions
   5. Never do this (negative constraints are surprisingly powerful)
   6. Schema context (top tables, grain, joins)

   Keep it under 200 lines. Beyond that the AI starts losing focus.
   If your rules need more, split with file-pattern scoping.
```

That is roughly 40 lines and it changes everything. The next time you ask the AI to write a dbt model, it knows your dialect, your layering, your tests, your naming, and your "do not do this" list. **The first draft will be 80% production-ready instead of 30%.**

```
   SAME PROMPT: "top customers by lifetime value"
   ──────────────────────────────────────────────────────────────────
   WITHOUT RULES                              WITH RULES (CLAUDE.md)
   ─────────────────                          ──────────────────────
   • generic ANSI SQL                         • Snowflake dialect
   • invented column names                    • real columns: fct_orders,
                                                 dim_customers
   • INNER JOIN where LEFT was needed         • LEFT JOIN on nullable FK
   • no NULL handling                         • explicit NULL handling
   • doesn't respect time window              • respects team's LTV definition
   → ~30% useful                              → ~90% useful
```

A few principles for writing your own rules file:

- **Be specific.** Avoid platitudes. "Write clean code" is useless. "Always use CTEs, never nested subqueries" is gold.
- **Encode your team's actual conventions**, not best practices from a blog. If your team uses tabs not spaces, write that. If your warehouse has weird naming, document it.
- **Lead with the stack.** The AI needs to know the dialect and framework before it can write a single useful line.
- **Include a "never do this" section.** Negative constraints are surprisingly powerful. They prevent the most common failure modes.
- **Keep it under 200 lines.** Beyond that the AI starts losing focus. If your rules need more, split into multiple files (Cursor's `.cursor/rules/*.mdc` supports this natively with file-pattern scoping).

> ⚠️ **No rules file at all** is the most common setup mistake. People download Cursor, get a few mediocre suggestions, and conclude *"AI tools don't work for my codebase."* They don't work yet, because you haven't told the AI what your codebase is. **A 30-line rules file is the single highest-ROI thing you can do this week.**

---

## Setting Up for SQL and Warehouse Work

Once the rules file is in place, the next leverage point is **exposing your schema to the AI**. The AI cannot write good SQL for tables it has never seen. It will invent column names that look plausible and get the JOIN keys wrong.

Three concrete patterns work, in increasing order of investment:

**Pattern 1: Inline schema in the prompt.** For ad-hoc queries, paste the relevant `CREATE TABLE` or dbt source definition into the chat. This works for one-off questions and is the cheapest way to get good output.

**Pattern 2: A schema context file in the repo.** Maintain a `docs/schema.md` (or use dbt's auto-generated `manifest.json`) that documents your core tables, columns, and relationships. Reference it in your rules file. Here is what a useful entry looks like:

```markdown
## marts.fct_orders

Grain: one row per order_id. ~50M rows, 12 months retained.

Columns:
- order_id (varchar, PK): unique order identifier
- customer_id (varchar, FK -> dim_customers): nullable for guest checkout
- order_status (varchar): one of {placed, paid, shipped, delivered, returned, cancelled}
- order_amount_usd (number(18,2)): gross order amount in USD
- placed_at (timestamp_tz): order placement time, UTC
- shipped_at (timestamp_tz): nullable until status >= shipped

Joins:
- fct_orders.customer_id = dim_customers.customer_id (left join, customer_id is nullable)
- fct_orders.order_id = fct_order_items.order_id (1:many)

Business notes:
- Returned orders keep their original order_amount_usd. Use fct_returns for refund amounts.
- Status 'cancelled' means cancelled before payment. Use 'returned' for post-delivery returns.
```

That context file turns the AI from "guesser" into "informed teammate." **A SQL prompt against this schema goes from 30% correct to 90% correct, in my experience.**

**Pattern 3: Connect AI directly to your warehouse via MCP.** Tools like Claude Code support the Model Context Protocol, which lets the AI query schema metadata, sample rows, and even run EXPLAIN plans on its own. This is the highest-fidelity option. It is also the one with the highest privacy bar, so check with your security team before pointing an AI tool at production credentials.

For dbt projects specifically: point your AI assistant at `target/manifest.json` after a `dbt parse`. That file contains every model, column, test, and relationship in your project. With manifest access, the AI can generate models that respect your existing DAG, reference real sources, and avoid the circular dependencies that always come up when AI invents references.

```
   SCHEMA EXPOSURE LADDER
   ──────────────────────
   Step 1: Inline schema in the prompt
          (paste CREATE TABLE for ad-hoc questions)
          → ~70% accurate
                       │
                       ▼
   Step 2: schema.md or dbt manifest in the repo
          → ~85% accurate
                       │
                       ▼
   Step 3: MCP connection to the warehouse
          (AI queries metadata + runs EXPLAIN itself)
          → ~95% accurate (security review required)

   Pick the step that matches how often you ask SQL questions.
```

---

## Setting Up for Python and Spark Development

For Python and Spark work, the setup goal is twofold: **give the AI strong static signals about your code, and give it consistent runtime context.**

### Use type hints aggressively
Type hints are documentation that the AI can actually read. A function with full type hints and a docstring gets 2–3× better suggestions than an untyped one. It is not magic. The AI just has more to work with.

```python
from datetime import datetime
from pyspark.sql import DataFrame, SparkSession

def dedupe_events_by_user(
    df: DataFrame,
    user_id_col: str = "user_id",
    timestamp_col: str = "event_at",
    keep: str = "latest",
) -> DataFrame:
    """Deduplicate events keeping one row per user.

    Args:
        df: input DataFrame with at least user_id_col and timestamp_col.
        user_id_col: column to partition by.
        timestamp_col: column to order by (must be a timestamp type).
        keep: 'latest' or 'earliest'. Default 'latest'.

    Returns:
        DataFrame with exactly one row per user_id, NULLs in timestamp_col
        treated as oldest.
    """
    ...
```

The AI now knows the inputs, the outputs, the NULL handling rule, and the default behavior. The next suggestion it makes will respect all of that.

### Set up your virtual environments deterministically
Use `uv` (or `poetry`, or `pip-tools`) with a pinned lockfile. AI assistants pick up on your `pyproject.toml` and `uv.lock` and will install or suggest versions that match. **Without a lockfile, the AI tends to suggest the latest version of every package, which breaks half your imports.**

### For PySpark, document your session config
Spark behavior changes dramatically based on cluster config (executor memory, shuffle partitions, AQE). If you keep a canonical `spark_session.py` in your repo and reference it in the rules file, the AI generates code that matches your real runtime:

```python
# spark_session.py
def get_session(app_name: str) -> SparkSession:
    return (
        SparkSession.builder
        .appName(app_name)
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.shuffle.partitions", "200")
        .config("spark.sql.autoBroadcastJoinThreshold", "100MB")
        .getOrCreate()
    )
```

Tell the AI *"all Spark jobs use the session from `spark_session.get_session()`,"* and you stop seeing suggestions that create their own ad-hoc SparkContext with conflicting settings.

---

## Setting Up for Pipeline and Orchestration Work

The orchestration layer (Airflow, Prefect, Dagster) is where AI productivity gains **compound the fastest**, because 60% of a DAG is boilerplate. The trick is giving the AI a template it can extend.

### Keep a canonical DAG template in your repo
Drop a `templates/dag_template.py` with your team's standard imports, default args, retries, on-failure callbacks, and tagging. Reference it in your rules file. The AI will use it as the starting point for every new DAG instead of inventing its own pattern.

```python
# templates/dag_template.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from acme.callbacks import slack_on_failure

default_args = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": slack_on_failure,
    "email_on_failure": False,
}

with DAG(
    dag_id="REPLACE_ME",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["domain:REPLACE_ME", "tier:REPLACE_ME"],
    max_active_runs=1,
) as dag:
    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")
    start >> end
```

Now when you ask the AI to *"create a DAG that ingests Stripe payments daily,"* it extends this template instead of inventing its own structure with different defaults, different callbacks, and different tagging.

### Wire AI into your CI/CD
AI-generated code is still code. It needs the same gates: linters, type checkers, unit tests, dbt CI runs, and SQL fluff. If your CI runs `ruff`, `mypy`, `sqlfluff`, and `dbt build` on every PR, the AI's suggestions get the same scrutiny as anyone else's. **This is the difference between "we use AI tools" and "we use AI tools safely."**

### Have an explicit AI code review step
Either a tag in the PR description (*"AI-assisted: yes"*), or a checklist that reviewers run through for AI-generated code. The point isn't to gatekeep, it's to remind humans to look for the failure modes AI is known for: silent JOIN fan-out, NULL handling, wrong materialization, business logic errors. We will cover the verification ritual in depth in **AI-Generated Code: When to Trust, When to Verify**.

```
   AI-GENERATED CODE GOES THROUGH THE SAME GATES AS HUMAN CODE
   ───────────────────────────────────────────────────────────

       ┌────────────────┐
       │   AI draft     │   (untrusted — dashed border)
       └───────┬────────┘
               │
       ┌───────▼────────┐
       │  ruff (lint)   │
       └───────┬────────┘
               │
       ┌───────▼────────┐
       │  mypy (types)  │
       └───────┬────────┘
               │
       ┌───────▼────────┐
       │ sqlfluff (SQL) │
       └───────┬────────┘
               │
       ┌───────▼────────┐
       │ dbt build      │
       └───────┬────────┘
               │
       ┌───────▼────────┐
       │ human review   │  ← joins, NULLs, business logic
       └───────┬────────┘
               │
       ┌───────▼────────┐
       │   PROD SHIP    │
       └────────────────┘
```

---

## Common Mistakes

These are the four setup mistakes I see over and over. Avoiding them is the difference between *"AI was meh"* and *"AI doubled my output."*

### 1. Not providing enough context
Most people prompt the AI like they prompt Google. *"Write a query to find top customers by revenue."* That prompt has no dialect, no schema, no time window, no business definition of "top," and no NULL handling. The AI fills in the blanks with statistical guesses, and the output is generic. **Always include: dialect, schema, sample data if useful, edge cases, and the specific business rule.**

### 2. Over-trusting AI output
*"It looks right"* is not verification. In my experience, AI-generated SQL is correct most of the time on simple queries, but a meaningful fraction has a silent bug. The setup mistake here is psychological: people treat AI output as authoritative because it is confidently worded and well-formatted. **Build a habit of reading every line, running on sample data, and checking row counts after joins.** AI confidence is unrelated to correctness.

### 3. Using AI for every task
Some tasks are faster to just type. Renaming a column, writing a single-line filter, fixing a typo. If reaching for the AI takes 20 seconds and the manual task takes 10, you are slowing yourself down. The skill is knowing when to invoke AI and when not to. **My rough rule: invoke AI when the task involves more than 3 lines of logic, or when I would have to look something up.**

### 4. Not customizing the rules file per project
Every project has different conventions. A rules file copied from a tutorial gives you generic suggestions. **Spend 30 minutes per project tailoring the rules file to your stack, schema, and team's habits. Update it when your conventions evolve.** This is the single most ignored, highest-ROI setup activity in the whole AI workflow.

---

## In an Interview

Setup is rarely a direct interview topic. Nobody is going to ask you *"describe your `.cursorrules` file"* in a system design round. But if AI tools come up (and they do, increasingly, in DE interviews at AI-forward companies), the way you talk about setup signals maturity.

- **Don't lead with setup. Lead with outcomes.** *"I use Cursor with a project-specific rules file that documents our Snowflake schema and dbt conventions. It cuts model development time by about 40%."*
- **If pressed, get specific.** Mention the rules file, the schema context, the type hints, the canonical templates. **Interviewers can tell the difference between someone who has actually configured these tools and someone who downloaded Cursor last week.**
- **Avoid sounding like a fan.** *"AI changed everything"* is a red flag. *"AI is a productivity tool that needs careful setup and verification"* is the senior engineer's framing.

---

## Try This

> Open your current project. Spend **30 minutes** writing a **10–30 line `CLAUDE.md` or `.cursorrules`** file. Cover four things: **stack** (warehouse, framework, language versions), **conventions** (naming, materialization, NULL handling), **schema** (your two or three most-queried tables with column descriptions), and a **"never do this" list.** Save it. Now run your next SQL or dbt prompt against it. **Compare the output to what you would have gotten without it.**

---

## Key Takeaways

- AI tools are downstream of context. The model is fixed. Your only lever is **setup**.
- For most DEs, default to **Cursor** or **Claude Code**. Use Copilot if your team is already on it. Don't tool-hop.
- The single highest-ROI setup activity is a **30–60 line rules file** (`CLAUDE.md` or `.cursorrules`) that documents your stack, conventions, schema, and "never do this" list.
- Expose your warehouse schema to the AI. Inline schema in prompts works for ad-hoc; a `docs/schema.md` or dbt `manifest.json` works for sustained productivity.
- **Type hints, docstrings, and pinned lockfiles** are AI-readable signals. Use them generously.
- **Canonical templates** (DAG template, Spark session, dbt model skeleton) compound across hundreds of prompts.
- Avoid the four setup mistakes: **no rules file, over-trusting output, using AI for every task, not customizing per project.**

> **Key Takeaway:** Setup is the difference between *"AI was meh"* and *"AI doubled my output."* Spend one focused afternoon on your rules file, schema context, and templates. The next month of work will be measurably faster, and every prompt you write after that benefits from the setup you did once.

---

## What Comes Next

> You have the environment. The next article, **Prompt Engineering for Data Engineers**, covers the patterns that turn a well-configured AI assistant into a production-grade code generator: schema context patterns, constraint specification, example-driven prompts, and the iterative refinement loop that beats trying to specify everything upfront.

---

*Written by **Gorijala Kiran** · Source: [datavidhya.com](https://datavidhya.com/learn/ai-for-data-engineering/)*
