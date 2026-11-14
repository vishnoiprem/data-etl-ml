# 7 — AI, ML and Agents in BigQuery

> **Practice Module 7 · BigQuery · 50 minutes**

## 🎯 What you will learn

- The four workflows BigQuery's AI capabilities are organised around, and what each one is
  actually for.
- How to call a large language model from SQL, and what the function signature really says.
- What embeddings and vector search are, and the mistake that invalidates a whole index.
- How a custom agent talks to BigQuery through MCP, and what "skills" are.
- How to get agent telemetry into a table you can query.

---

## 🧠 Concept

BigQuery provides AI, machine learning and agent capabilities across several workflows. Knowing
which workflow you are in is most of the answer.

| Workflow | What it is | Who uses it |
|---|---|---|
| **In-console assistance and analysis** | Assistance in the console and Colab Enterprise notebooks | Analysts, engineers |
| **AI, search and ML in SQL queries** | LLMs, text/vector search and predictive ML inside GoogleSQL | Everyone writing queries |
| **Tools for building agents** | MCP servers, agent frameworks, skills, agent analytics | Agent builders |
| **Agents in your IDE or terminal** | Query data, manage pipelines, run workflows from VS Code, Antigravity, CLIs | Developers |

> Availability varies by **BigQuery edition**. Check the current documentation for which
> features your edition includes before promising them to a stakeholder.

### Workflow 1 — In-console assistance and analysis

Inside the Google Cloud console and Colab Enterprise notebooks:

| Capability | What it does |
|---|---|
| **SQL code assist** | Generates, completes and explains GoogleSQL in the query editor |
| **Python code assist** | Assists with Python, PySpark and BigQuery DataFrames |
| **Data canvas** | Finds tables, joins data, runs SQL or natural-language requests, and visualises results in a DAG workspace |
| **Data insights** | Creates natural-language questions and the corresponding SQL from table metadata |
| **Data preparation** | Proposes context-aware cleaning, transformation and enrichment actions |
| **Interactive SQL translator** | Creates custom rules for translating other SQL dialects into GoogleSQL |
| **Conversational analytics** | Answers questions about table data and returns answers and visualisations |
| **Gemini Cloud Assist** | *(Preview)* Resource discovery, lineage tracing, job debugging, reservation and slot analysis, query optimisation, query scheduling |
| **Data Science Agent** | Automates exploratory analysis, cleaning, ML work and visualisation for BigQuery tables and CSV files |
| **Data Engineering Agent** | Creates, changes and troubleshoots Dataform pipelines through natural-language prompts |

**Conversational analytics** deserves special attention, because it changes the governance
question. It can use configured **data agents** — with custom metadata, glossary terms,
instructions and **verified queries**. The agent writes *and runs* SQL.

That last part is the point: a data agent with verified queries is how you let an assistant
answer questions **without** letting it write arbitrary SQL against production tables. The
verified queries are the allowlist. If you skip that step, you have given a language model
production credentials and called it a feature.

### Workflow 2 — AI, search and ML in GoogleSQL

Three families of function:

**General-purpose AI functions** — you control the model, the prompt, the output schema and the
parameters.

**Managed AI functions** — simplify routine filtering, rating, classification and aggregation.
BigQuery picks the model for cost and quality.

**Task-specific functions** — invoke Cloud AI APIs for natural-language processing, translation,
document processing, audio transcription and computer vision.

#### Calling an LLM from SQL

The canonical function is `ML.GENERATE_TEXT`. Its full signature for Gemini:

```sql
ML.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.MODEL`,
  { TABLE `PROJECT_ID.DATASET.TABLE` | (QUERY_STATEMENT) },
  STRUCT(
    {
      [MAX_OUTPUT_TOKENS AS max_output_tokens]
      [, TOP_P AS top_p]
      [, TEMPERATURE AS temperature]
      [, STOP_SEQUENCES AS stop_sequences]
      [, GROUND_WITH_GOOGLE_SEARCH AS ground_with_google_search]
      [, SAFETY_SETTINGS AS safety_settings]
    }
    |
    [, MODEL_PARAMS AS model_params]
    [, FLATTEN_JSON_OUTPUT AS flatten_json_output]
    [, REQUEST_TYPE AS request_type]
  )
)
```

The details that matter:

- The input is either a **table** whose relevant column is named `prompt`, or a
  **query statement** that must produce a column named `prompt`.
- The model is referenced as `MODEL \`PROJECT_ID.DATASET.MODEL\`` — a **remote model** object.
  **The remote model and its input table must be in the same region.**
- `MAX_OUTPUT_TOKENS`, `TOP_P`, `TEMPERATURE`, `STOP_SEQUENCES`, `GROUND_WITH_GOOGLE_SEARCH` and
  `SAFETY_SETTINGS` control the Gemini call.
- `REQUEST_TYPE` selects quota behaviour: `DEDICATED`, `SHARED` or `UNSPECIFIED`.
- `FLATTEN_JSON_OUTPUT` parses the returned JSON into separate columns.
- The variants differ by provider: **Gemini** takes `GROUND_WITH_GOOGLE_SEARCH` and
  `SAFETY_SETTINGS`; **Claude** takes `TOP_K` instead of `TEMPERATURE`; **Llama** and
  **Mistral AI** take `MAX_OUTPUT_TOKENS`, `TOP_P`, `TEMPERATURE` and `STOP_SEQUENCES`; **open
  models** additionally support `USE_CHAT_MODE`.

A worked example:

```sql
SELECT *
FROM ML.GENERATE_TEXT(
  MODEL `mydataset.gemini_model`,
  (SELECT 'What is the purpose of dreams?' AS prompt)
);
```

The underlying model is confirmed through the model details page's **Remote endpoint** field.

#### Embeddings and vector search

**Embeddings** numerically represent text, images, audio, video, PDFs or model-derived features,
so that related content lies close together in the embedding space.

| Function | Does |
|---|---|
| `AI.EMBED` | Generates **one** embedding |
| `AI.GENERATE_EMBEDDING` | Generates a **column** of embeddings |
| `VECTOR_SEARCH` | Searches stored embeddings |
| `AI.SEARCH` | Searches tables using autonomous embedding generation |
| `AI.SIMILARITY` | Computes **cosine similarity**; best for a small number of comparisons |

`ML.GENERATE_EMBEDDING` has this signature:

```sql
ML.GENERATE_EMBEDDING(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  { TABLE `PROJECT_ID.DATASET.TABLE_NAME` | (QUERY_STATEMENT) },
  [STRUCT(...)]
)
```

- The model may be a remote embedding model, or a PCA, autoencoder or matrix-factorization
  model.
- The input normally needs a `STRING` column named `content`; a query can alias another column
  to that name.
- The output column is **`ml_generate_embedding_result`** — normally an `ARRAY<FLOAT64>` when
  JSON flattening is enabled — plus `ml_generate_embedding_status`.
- Model-dependent `STRUCT` options include `flatten_json_output`, `task_type`,
  `output_dimensionality`, video time-segment options and `trial_id`.

Search without an index is **brute-force** distance measurement over every record. A **vector
index** enables approximate nearest-neighbour search using technologies such as **IVF** and
**ScaNN** — faster, but the results become approximate and **recall may decrease**.

> **The mistake that invalidates everything.** Embeddings from different models or model
> versions occupy **separate spaces and are generally mathematically incompatible**. When you
> change models you must: regenerate the stored embeddings, update the search-time embedding
> generation, and recreate or rebuild the vector indexes.
>
> Skip any one of those three and your search returns confident nonsense. This is worth knowing
> before an interviewer finds it for you, because it is the exact failure mode of a system that
> worked in development.

#### BigQuery ML

`CREATE MODEL` trains a model inside the warehouse; `ML.PREDICT` runs inference on it. The
core functions are `ML.PREDICT`, `ML.EVALUATE`, `ML.TRAINING_INFO` and `ML.ROC_CURVE`. Named
models include **TimesFM**, **ARIMA_PLUS**, **ARIMA_PLUS_XREG** and the preview **TabFM**. The
platform also supports **explainable AI** and **contribution analysis**.

BigQuery ML covers forecasting and anomaly detection, classification and regression, clustering,
dimensionality reduction, and recommendations — through GoogleSQL, the console, the `bq` tool,
the REST API and Colab Enterprise notebooks.

### Workflow 3 — Tools for building agents

| Tool | What it gives an agent |
|---|---|
| **BigQuery MCP server** | Lists resources, inspects table metadata, and executes SQL |
| **BigQuery Migration Service MCP server** | Converts SQL to GoogleSQL and generates DDL |
| **BigQuery Data Transfer Service MCP server** | Configures and monitors transfers |
| **MCP Toolbox for Databases** | An open-source local MCP server, including **parameterized custom SQL tools** |
| **ADK integrations** | Prebuilt BigQuery toolsets for agents |
| **BigQuery agent skills** | Reusable packages named `bigquery-basics` and `bigquery-ai-ml` |
| **BigQuery agent analytics** | Streams interaction logs from ADK or LangGraph into BigQuery |

**MCP — the Model Context Protocol** — is the standard that lets an agent discover and call
tools. The BigQuery MCP server is the bridge: an agent asks it to list resources, inspect table
metadata, or execute SQL, and the server performs those actions against your project with
your credentials.

**Agent skills** (`bigquery-basics`, `bigquery-ai-ml`) are reusable packages of instructions and
references that teach an agent *how* to work with BigQuery correctly — the conventions, the
function names, the gotchas. They are the difference between an agent that writes BigQuery and
an agent that writes *good* BigQuery.

**Agent analytics** closes the loop. It streams interaction logs from ADK or LangGraph into
BigQuery for analysis of **requests, responses, tool calls, errors, token usage, latency and
execution traces**. Logs can also be sent through the **BigQuery Storage Write API using gRPC**.

This is the piece that makes agent usage governable. Without telemetry, an agent that starts
issuing expensive queries is invisible. With it, the queries land in a table, and you can write
the same `maximumBytesBilled` guardrail and the same alerting you would write for a human
user.

### Workflow 4 — Agents in your IDE or terminal

**Data Agent Kit** provides IDE extensions for **VS Code, Antigravity and Cursor**, plus
coding-agent plugins for **Antigravity CLI, Gemini CLI, Claude Code and Codex CLI**. These can
explore datasets, run queries, build pipelines and train ML models.

**MCP IDE integrations** connect Antigravity, VS Code, Cursor, Windsurf and Claude Code through
the **Antigravity MCP Store** or **MCP Toolbox for Databases**.

**Antigravity CLI** runs queries, manages pipelines and interacts with BigQuery resources
directly from a terminal.

### AutoMode

BigQuery's automatic query-planning mode — covered in detail in
[module 4](04-querying-and-internals.md). The one thing to add here: as query shapes get more
complex (joins, CTEs, window functions), auto-planning becomes more valuable, because there are
more plan choices for the optimiser to make and fewer for you to get wrong.

---

## 🛠️ Hands-On

### 💻 Runs locally — what "no data movement" is worth

The AI/ML pitch is often "no data movement". Here is what that means in bytes and dollars,
using the course's own cost model.

```python
import sys
sys.path.insert(0, "../project/core")
from cost_model import estimate

TABLE_TB = 50.0

# The classic ML path: copy the warehouse into a training environment, then read it back.
extract = estimate("cloud-storage", storage_gb=TABLE_TB * 1024,
                   egress_gb=TABLE_TB * 1024, apply_free_tier=False).total
train = estimate("vertex-ai", training_node_hours=10, apply_free_tier=False).total

# The BigQuery ML path: the data never leaves the warehouse.
bqml = estimate("bigquery", scanned_tb=TABLE_TB, slot_hours=10,
                apply_free_tier=False).total

print(f"extract + egress + train: ${extract + train:,.2f}")
print(f"BigQuery ML, same data:    ${bqml:,.2f}")
print(f"ratio:                     {(extract + train) / bqml:.0f}x")
```

Expected output:

```text
extract + egress + train: $7,204.70
BigQuery ML, same data:    $313.10
ratio:                     23x
```

The egress is the killer — and it is a cost people forget entirely, because it appears on the
storage bill rather than the compute bill. **BigQuery ML's real advantage is not convenience.
It is that the data never crosses a network boundary, so it never gets billed for crossing
one.**

### 🌐 Needs a BigQuery project — call a model from SQL

First, create the remote model:

```sql
CREATE MODEL `YOUR_PROJECT_ID.YOUR_DATASET.gemini_model`
REMOTE OPTIONS (
  endpoint = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash'
);
```

Then call it:

```sql
SELECT
  ml_generate_text_result,
  ml_generate_text_status
FROM ML.GENERATE_TEXT(
  MODEL `YOUR_PROJECT_ID.YOUR_DATASET.gemini_model`,
  (SELECT 'Summarise this in one sentence: BigQuery is a serverless data warehouse.' AS prompt),
  STRUCT(0.8 AS temperature, 256 AS max_output_tokens)
);
```

And the pattern that actually matters — a prompt column over a table:

```sql
SELECT
  transaction_id,
  ml_generate_text_result AS summary
FROM ML.GENERATE_TEXT(
  MODEL `YOUR_PROJECT_ID.YOUR_DATASET.gemini_model`,
  (SELECT transaction_id, CONCAT('Describe this transaction: ', sales_amount) AS prompt
   FROM `YOUR_PROJECT_ID.YOUR_DATASET.sales`
   WHERE sale_date = '2026-11-13'),
  STRUCT(0.2 AS temperature, 128 AS max_output_tokens)
);
```

**`temperature` is a cost and determinism control, not just a creativity dial.** At `temperature
= 0` the same prompt produces the same output far more reliably — which is what you want when
the output feeds a downstream table. At `0.8` you get variety, which is what you want for
brainstorming. For anything in a pipeline, keep it low.

### 🌐 Needs a BigQuery project — embeddings and vector search

```sql
-- 1. Generate embeddings for a column.
CREATE TABLE `YOUR_PROJECT_ID.YOUR_DATASET.product_embeddings` AS
SELECT
  product_id,
  product_name,
  ml_generate_embedding_result AS embedding
FROM ML.GENERATE_EMBEDDING(
  MODEL `YOUR_PROJECT_ID.YOUR_DATASET.text_embedding_model`,
  (SELECT product_id, product_name AS content
   FROM `YOUR_PROJECT_ID.YOUR_DATASET.products`),
  STRUCT(flatten_json_output => TRUE)
);
```

Note the aliasing: the source column is `product_name`, and the query aliases it to
**`content`** — which is the column name the function expects.

```sql
-- 2. Build a vector index over it.
CREATE VECTOR INDEX `YOUR_PROJECT_ID.YOUR_DATASET.product_embeddings_index`
ON `YOUR_PROJECT_ID.YOUR_DATASET.product_embeddings`(embedding);
```

```sql
-- 3. Search.
SELECT product_id, product_name, distance
FROM VECTOR_SEARCH(
  (SELECT * FROM `YOUR_PROJECT_ID.YOUR_DATASET.product_embeddings` WHERE product_name = 'Wireless Mouse'),
  (SELECT ml_generate_embedding_result FROM ML.GENERATE_EMBEDDING(
     MODEL `YOUR_PROJECT_ID.YOUR_DATASET.text_embedding_model`,
     (SELECT 'a computer pointing device' AS content))),
  top_k => 5,
  distance_threshold => 0.3
)
ORDER BY distance;
```

**The search-time embedding must come from the same model as the stored embeddings.** Generate it
in the query, as above — do not cache it from a different model version.

### 🌐 Needs a BigQuery project — a data-quality agent with verified queries

This is the governed way to let an assistant answer questions about your data. Configure a
**data agent** with custom metadata, glossary terms, instructions and **verified queries** —
then the agent writes and runs SQL *within that boundary*.

```sql
-- A verified query: the agent is allowed to use this, and only this shape of query.
SELECT
  store_id,
  SUM(sales_amount) AS revenue,
  COUNT(*)          AS transactions
FROM `YOUR_PROJECT_ID.YOUR_DATASET.sales`
WHERE sale_date = @sale_date
GROUP BY store_id
ORDER BY revenue DESC;
```

The governance story to tell: the agent **cannot** invent arbitrary SQL against production
tables. It composes from a reviewed set. Without that boundary, you have handed a language
model production credentials and no audit trail of what it ran — except, with agent analytics,
you do get the trail.

### 🌐 Needs a BigQuery project — agent analytics

```sql
CREATE TABLE `YOUR_PROJECT_ID.YOUR_DATASET.agent_interaction_logs` (
  interaction_id STRING,
  agent_name     STRING,
  session_id     STRING,
  request_json   JSON,
  response_json  JSON,
  tool_calls     ARRAY<STRUCT<name STRING, arguments JSON, status STRING>>,
  error_message  STRING,
  token_count    INT64,
  latency_ms     INT64,
  logged_at      TIMESTAMP
)
PARTITION BY DATE(logged_at)
CLUSTER BY agent_name;
```

Populated by the agent analytics stream from ADK or LangGraph, or by the Storage Write API
using gRPC. Then query it like any other table:

```sql
SELECT
  agent_name,
  COUNT(*)                  AS interactions,
  COUNTIF(error_message IS NOT NULL) AS errors,
  ROUND(AVG(latency_ms))   AS avg_latency_ms,
  SUM(token_count)          AS total_tokens
FROM `YOUR_PROJECT_ID.YOUR_DATASET.agent_interaction_logs`
WHERE logged_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY agent_name
ORDER BY total_tokens DESC;
```

**That query is the governance story.** Now you can answer: which agent is spending the most,
which is failing, and which is slow. Without it, agent usage is invisible until the bill
arrives.

### 🌐 Needs a BigQuery project — BigQuery ML

```sql
CREATE MODEL `YOUR_PROJECT_ID.YOUR_DATASET.customer_churn`
OPTIONS (
  model_type = 'LOGISTIC_REGRESSION',
  input_label_cols = ['churned'],
  data_split_method = 'AUTO_SPLIT',
  enable_explain_ai = TRUE
) AS
SELECT
  churned,
  tenure_months,
  monthly_spend,
  support_tickets
FROM `YOUR_PROJECT_ID.YOUR_DATASET.customer_features`;
```

Then predict, and — importantly — evaluate against something trivial:

```sql
SELECT predicted_churned, COUNT(*) AS customers
FROM ML.PREDICT(
  MODEL `YOUR_PROJECT_ID.YOUR_DATASET.customer_churn`,
  (SELECT tenure_months, monthly_spend, support_tickets
   FROM `YOUR_PROJECT_ID.YOUR_DATASET.customers_current`)
)
GROUP BY predicted_churned;
```

Always compare against a trivial baseline. **If a linear model over two features does not beat
"predict the average", the model is not earning its complexity.** This is the single most
important discipline in applied ML, and it is the one most often skipped.

---

## 🛠️ Common Errors and Fixes

**"The remote model and the table must be in the same region."**

The remote model object and its input table must be in the same region. Move one of them, or
create the model in the same region as the data. This is a hard constraint, not a warning.

**"ML.GENERATE_TEXT returns an error: 'Column named prompt not found'."**

The input must have a column named `prompt`. If your column is called something else, alias it:

```sql
(SELECT transaction_id, CONCAT('...', sales_amount) AS prompt FROM ...)
```

**"My vector search returns results that make no sense."**

Almost certainly **embedding space mismatch**. The stored embeddings and the query embedding
came from different models or different model versions. Regenerate the stored embeddings, update
the search-time generation, and rebuild the index — all three.

**"Vector search is slow."**

You are probably searching without an index, so BigQuery is doing brute-force distance
measurement over every record. Create a `VECTOR INDEX`. Also note that the index makes results
**approximate** — recall decreases. That is a trade, not a bug.

**"The agent produced SQL that referenced a table I did not authorise."**

The data agent was configured without **verified queries**, so the agent wrote free-form SQL.
Add verified queries as the allowlist. Then the agent composes from reviewed material only.

**"Our agent costs are unpredictable."**

Set `maximumBytesBilled` on the queries the agent runs, and route agent interaction logs into
BigQuery so you can attribute spend to a specific agent and tool call.

**"BigQuery ML gives a different result than my training pipeline."**

Check for **training-serving skew**: features computed differently at training and serving time.
It works offline and fails in production, and it is the most common way a model that validated
well gets quietly worse.

---

## 💡 Production Notes

### How to introduce AI into a data pipeline without losing control

The sequence that works:

1. **Start with the prebuilt model** to get a baseline and a working pipeline. Do not begin with
   a custom model.
2. **Put the AI call behind a table.** `ML.GENERATE_TEXT` writes to a column or a table. Every
   downstream consumer reads the table, not the model. This means the AI can be replaced,
   re-run or audited without touching anything else.
3. **Keep `temperature` low in pipelines.** Variety is for humans; determinism is for machines.
4. **Build the evaluation set before the model.** A model with no evaluation set is not
   deployed. Ever.
5. **Compare against a trivial baseline** every time.

### What an agent needs before you let it near production

- [ ] **Scoped credentials.** A dedicated service account with read-only access to the datasets
      the agent needs, and nothing else.
- [ ] **Verified queries** as the allowlist, wherever the agent writes SQL.
- [ ] **`maximumBytesBilled`** on every query it can run.
- [ ] **Agent analytics** enabled, with the logs landing in a table.
- [ ] **An alert** on agent spend, error rate and latency.
- [ ] **A kill switch** — the ability to revoke the agent's access in one command.

That last one is the difference between "we deployed an agent" and "we deployed an agent we can
stop".

### Where MCP fits in the architecture

MCP is the *interface* layer between an agent and BigQuery. It is what makes an agent portable:
the same agent, pointed at a different MCP server, works against a different database. The
tools you expose through MCP are your security boundary — an agent can only do what its tools
allow.

**Parameterised custom SQL tools** in the MCP Toolbox for Databases are worth understanding,
because they are the difference between an agent that can run arbitrary SQL and one that can
run *your* vetted queries with *your* parameters.

### The honest framing for an interview

> "BigQuery now covers the whole AI surface — LLM calls and vector search in SQL, BigQuery ML,
> MCP servers for agents, agent telemetry as a table. My view is that the interesting work has
> moved from *can we call a model* to *how do we keep the agent's queries bounded, priced and
> auditable*. That is a data engineering problem, not a machine learning one, and it is the
> problem I would want to own."

---

## 🔑 Key Takeaways

- Four workflows: **in-console assistance**, **AI/ML in SQL**, **tools for building agents**,
  **agents in IDE/terminal**. Availability varies by BigQuery edition.
- **`ML.GENERATE_TEXT(MODEL \`proj.ds.model\`, input, STRUCT(...))`** — the input needs a
  column named `prompt`; the model and its input table must be in the **same region**.
- `MAX_OUTPUT_TOKENS`, `TOP_P`, `TEMPERATURE`, `STOP_SEQUENCES`, `GROUND_WITH_GOOGLE_SEARCH`,
  `SAFETY_SETTINGS`; `REQUEST_TYPE` for quota; `FLATTEN_JSON_OUTPUT` for structured output.
- **Embeddings from different models are incompatible.** Change model ⇒ regenerate embeddings,
  update search-time generation, rebuild the index. All three.
- `AI.EMBED`, `AI.GENERATE_EMBEDDING`, `VECTOR_SEARCH`, `AI.SEARCH`, `AI.SIMILARITY` (cosine).
- `ML.GENERATE_EMBEDDING` reads a column named **`content`** and writes
  **`ml_generate_embedding_result`**.
- A vector index (IVF, ScaNN) makes search faster and results **approximate** — recall drops.
- **MCP** is how agents reach BigQuery: the BigQuery MCP server lists resources, inspects table
  metadata and executes SQL. Your exposed tools are your security boundary.
- **Agent skills** (`bigquery-basics`, `bigquery-ai-ml`) teach an agent how to work with
  BigQuery correctly.
- **Agent analytics** streams ADK/LangGraph interaction logs into BigQuery — requests, tool
  calls, errors, token usage, latency, traces.
- Always compare a model against a trivial baseline before deploying it.

---

## 📚 Practice Exercises

1. Write a one-paragraph explanation of `ML.GENERATE_TEXT` for an engineer who knows SQL but
   not ML. Your paragraph must mention the `prompt` column name, the remote model reference, the
   same-region constraint, and one `STRUCT` option.

2. Build the full embedding pipeline on real data: generate embeddings, create a vector index,
   and run a search. Then change the embedding model and observe what breaks. Document exactly
   which of the three steps you must repeat, and what the search returns if you skip each one.

3. Explain the difference between a vector index and an exact search, in terms of latency,
   recall and cost. Then write the sentence you would use to explain to a product owner why
   search results might differ slightly between two runs.

4. Design the MCP tool surface for an agent that answers revenue questions. List each tool, its
   parameters, and whether it is read-only. Then explain what an attacker or a confused agent
   could do with each one, and how your parameterisation choices limit the damage.

5. Configure a data agent with verified queries for a retail warehouse. Write five verified
   queries, and then write the three questions a business user would ask that your agent must
   *not* be able to answer. Explain what happens in each case.

6. Use the agent analytics table to write three governance dashboards: one on spend by agent,
   one on error rate, and one on latency. Then write the alert thresholds you would set and
   justify each number.

7. Train a BigQuery ML model, evaluate it against a trivial baseline, and explain the result. If
   the model does not beat the baseline, say so plainly and propose what to do next — this is
   the expected outcome more often than people admit.

8. Write the two-minute answer to "how do you keep an AI agent within budget and within
  permission in a BigQuery environment?" Your answer must cover credentials, verified queries,
  `maximumBytesBilled`, agent analytics, and a kill switch, and it must say why each one is
  necessary rather than listing them.

---

## 📖 Further Reading

- [Introduction to BigQuery AI](https://docs.cloud.google.com/bigquery/docs/ai-introduction)
- [Introduction to vector search](https://docs.cloud.google.com/bigquery/docs/vector-search-intro)
- [Create machine learning models in BigQuery ML](https://docs.cloud.google.com/bigquery/docs/create-machine-learning-model)
- [Creating and training models](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create)
- [Feature preprocessing](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-preprocess-overview)
- [End-to-end journey for machine learning models](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-e2e-journey)
- [BigQuery docs home](https://docs.cloud.google.com/bigquery/docs)
- [Course interview bank: Governance, Security and ML](../interview/06-governance-security-and-ml.md)
