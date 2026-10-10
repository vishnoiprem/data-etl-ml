# Section 12 — Cortex AI & Machine Learning

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L86–L99
> **Duration:** ~110 min

This is the longest single section in the course, and the most
forward-looking. We start with **Snowpipe error handling** (the
natural close of the loading story) and then spend the rest of the
section on **Snowflake Cortex** — the AI/ML surface that lives
inside Snowflake.

Cortex is a family of services, not a single thing:

- **AI SQL functions** — call LLMs and ML models from `SELECT`.
  `SENTIMENT`, `SUMMARIZE`, `TRANSLATE`, `EXTRACT_ANSWER`, `CLASSIFY`.
- **Cortex Search** — managed, serverless hybrid (keyword +
  vector) search over your text.
- **Cortex Analyst** — a text-to-SQL agent that turns natural
  language questions into SQL against a semantic model.
- **Snowflake ML** — Bring-your-own-model + native feature store
  + model registry, all running on your warehouse compute.
- **Snowflake Notebooks** — Python notebooks in the Snowflake UI
  with first-class access to Snowpark.
- **Streamlit in Snowflake** — internal apps against Snowflake
  data, with no separate infra.

The second half of the section is one long **hands-on scenario**:
load a customer-feedback dataset, run Text AI over it, score with an
LLM function, analyze media, and serve a Cortex Search service from
a Streamlit app.

| L# | Title | Min |
|---|---|---|
| L86 | Error handling for Snowpipe loads | 7:00 |
| L87 | Snowflake Cortex AI - Overview | 7:30 |
| L88 | AI SQL Functions | 8:30 |
| L89 | Cortex Search | 8:00 |
| L90 | Cortex Analyst | 8:00 |
| L91 | Snowflake ML | 7:30 |
| L92 | Snowflake Notebooks | 6:00 |
| L93 | Streamlit in Snowflake | 6:00 |
| L94 | Hands-on: Overview Of Scenario | 5:00 |
| L95 | Hands-on: Load The Data | 8:00 |
| L96 | Hands-on: Text AI | 9:00 |
| L97 | Hands-on: LLM Function | 9:00 |
| L98 | Hands-on: Media AI Analytics | 8:00 |
| L99 | Hands-on: Cortex Service | 12:00 |

## Key concepts you'll need later

- **Cortex** = Snowflake's AI/ML surface. Runs on Snowflake-managed
  compute; you don't ship data out of Snowflake.
- **AI SQL functions** — `SNOWFLAKE.CORTEX.SENTIMENT(...)` and
  friends. Per-row, per-call pricing.
- **Cortex Search service** — managed hybrid search index over a
  table. REST API for retrieval.
- **Cortex Analyst** — semantic model YAML + a REST endpoint that
  converts text to SQL.
- **Snowflake ML** — `MODEL` registry, feature store, Snowpark
  Python training on warehouse compute.
- **Notebooks + Streamlit** — the in-Snowflake IDE surface for
  building and serving.

## What comes next

Section 13 is **Snowpipe for Azure** — the same pipe story we just
finished on GCS, but on Azure Blob with an Event Grid notification
integration.
