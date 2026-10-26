---
l_id: L93
title: Streamlit in Snowflake
duration: "6:00"
prereqs: ["L92 - Snowflake Notebooks"]
---

# L93 — Streamlit in Snowflake

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 12 — Cortex AI & Machine Learning
> **Duration:** 6:00

## Prereqs

A role with `USAGE` on a warehouse and the
`CREATE STREAMLIT APP` privilege on a schema.

## Lecture

**Streamlit in Snowflake** lets you ship an internal data app that
runs entirely inside Snowflake. No external service to host, no
network rule to write, no OAuth integration to maintain. The app
talks to a Snowpark session; the user sees a URL like
`https://<account>.snowflakecomputing.com/streamlit-app/...`.

### Create an app from the UI

`Projects → Streamlit → + Streamlit App`. Pick the warehouse the
app will use to run queries.

### Or create from SQL

```sql
CREATE STREAMLIT ml.review_dashboard
  FROM '@ml.streamlit/review_dashboard.py'
  MAIN_FILE = 'review_dashboard.py'
  QUERY_WAREHOUSE = 'compute_wh';
```

The `STREAMLIT` object is metadata; the file is a single
`streamlit_app.py` on a stage.

### A minimal app

```python
# streamlit_app.py
import streamlit as st
from snowflake.snowpark.context import get_active_session

session = get_active_session()

st.title("Customer Reviews — Sentiment")

limit = st.slider("Rows to show", 10, 1000, 100)

df = session.sql(f"""
  SELECT review_id,
         review_text,
         SNOWFLAKE.CORTEX.SENTIMENT(review_text) AS sentiment
  FROM raw.customer_reviews
  ORDER BY review_date DESC
  LIMIT {limit}
""").to_pandas()

st.dataframe(df, use_container_width=True)
st.bar_chart(df["sentiment"].clip(-1, 1))
```

That's the whole app. `get_active_session()` gives you a live
session with the role of the user who opened the app — so row
access policies and column masking policies apply automatically.

### The widgets

Standard Streamlit widgets work:

```python
date = st.date_input("From")
region = st.multiselect("Region", ["NA", "EMEA", "APAC"])
prompt = st.text_area("Ask the data")
```

The widget state is per-user. Use `st.session_state` for things
that should survive a rerun (chat history, current selection).

### Caching expensive calls

```python
@st.cache_data
def load_summary():
    return session.sql("SELECT region, COUNT(*) AS n FROM ... GROUP BY 1").to_pandas()

df = load_summary()
```

`@st.cache_data` keeps the result in memory across reruns and
users, so the warehouse isn't hit on every widget tweak.

### Security model

- **Authentication** — whoever opens the URL must be a Snowflake
  user (or use external OAuth).
- **Authorization** — the app runs with the opener's role, so
  masking and row access policies apply.
- **Network** — the app runs in Snowflake's infra; the user does
  not get direct database access from outside Snowflake.

### Limitations

- One warehouse per app.
- Streamlit version lags the open-source release by a few weeks.
- No external network calls without a network rule. (This is
  actually a feature.)

## Key takeaways

- `CREATE STREAMLIT` + a single `.py` file = an internal app.
- The app runs with the opener's role; RLS and masking work.
- Use `@st.cache_data` to avoid hammering the warehouse on widget
  changes.

## What's next

In **L94 — Hands-on: Overview Of Scenario** we start a single
end-to-end Cortex scenario that we will build across L94–L99.
