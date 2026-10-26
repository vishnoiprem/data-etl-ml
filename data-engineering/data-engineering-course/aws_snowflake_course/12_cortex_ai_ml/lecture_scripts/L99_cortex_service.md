---
l_id: L99
title: Hands-on: Cortex Service
duration: "12:00"
prereqs: ["L98 - Hands-on: Media AI Analytics"]
---

# L99 — Hands-on: Cortex Service

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Section:** 12 — Cortex AI & Machine Learning
> **Duration:** 12:00

## Prereqs

The scored view from L98. A role with `CREATE CORTEX SEARCH
SERVICE`, `CREATE STREAMLIT`, and a warehouse.

## Lecture

We close the scenario with two artifacts: a **Cortex Search
service** for retrieval over the reviewed text, and a **Streamlit
app** that uses it to power a triage dashboard.

### Part 1 — Cortex Search service

Build a search service over the English-translated text so the
app's "search reviews" box can find relevant feedback fast.

```sql
USE SCHEMA ml;

CREATE OR REPLACE CORTEX SEARCH SERVICE review_search
  ON english_text
  ATTRIBUTES product, sentiment_label, image_label
  WAREHOUSE = ai_demo_wh
  TARGET_LAG = '1 hour'
AS (
  SELECT review_id,
         english_text,
         product,
         sentiment_label,
         image_label
  FROM analytics.scored.customer_reviews
  WHERE english_text IS NOT NULL
);
```

Query it from SQL first:

```sql
SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
  'ml.review_search',
  'broken screen on the laptop',
  LIMIT => 5
) AS hits;
```

You should see relevant reviews come back with `product`,
`sentiment_label`, and `image_label` already attached.

### Part 2 — Streamlit app

Create a new app:

```sql
USE SCHEMA app;

CREATE OR REPLACE STREAMLIT review_triage
  FROM '@app.streamlit/review_triage.py'
  MAIN_FILE = 'review_triage.py'
  QUERY_WAREHOUSE = 'ai_demo_wh';
```

The body of the app:

```python
# review_triage.py
import streamlit as st
from snowflake.snowpark.context import get_active_session

session = get_active_session()

st.set_page_config(page_title="Review Triage", layout="wide")
st.title("Customer Review Triage")

# --- sidebar filters ---------------------------------------------------------
sentiment = st.sidebar.multiselect(
    "Sentiment",
    ["POSITIVE", "NEUTRAL", "NEGATIVE"],
    default=["NEGATIVE", "NEUTRAL"],
)
img_labels = st.sidebar.multiselect(
    "Image label",
    ["DAMAGED_PACKAGE", "BUG_SCREENSHOT", "RECEIPT", "PRODUCT_PHOTO", "OTHER"],
)
products = st.sidebar.multiselect(
    "Product",
    session.sql(
        "SELECT DISTINCT product FROM analytics.scored.customer_reviews"
    ).to_pandas()["PRODUCT"].tolist(),
)

# --- search box --------------------------------------------------------------
query = st.text_input("Search reviews", "")

@st.cache_data(ttl=300)
def search(q, sent, imgs, prods):
    if not q:
        return session.sql("""
          SELECT review_id, product, sentiment_label, image_label, english_text, draft_reply
          FROM analytics.scored.customer_reviews
          WHERE sentiment_label IN ({})
          ORDER BY review_date DESC
          LIMIT 50
        """).to_pandas()
    # Use Cortex Search for retrieval
    res = session.sql(
        f"SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW('ml.review_search', '{q}', LIMIT => 50) AS hits"
    ).collect()[0]["HITS"]
    import json
    return pd.DataFrame(json.loads(res)["results"])

import pandas as pd
df = search(query, sentiment, img_labels, products)
df = df[df["SENTIMENT_LABEL"].isin(sentiment) if sentiment else True]

st.dataframe(df, use_container_width=True, height=600)

# --- detail view -------------------------------------------------------------
st.subheader("Draft reply")
selected = st.selectbox("Pick a review to triage", df["REVIEW_ID"].tolist())
if selected:
    row = df[df["REVIEW_ID"] == selected].iloc[0]
    st.write("**Original text**", row["ENGLISH_TEXT"])
    st.write("**Image label**", row["IMAGE_LABEL"])
    st.write("**Draft reply**", row["DRAFT_REPLY"])
    edited = st.text_area("Edit and send", value=row["DRAFT_REPLY"] or "")
    if st.button("Mark as triaged"):
        session.sql(
            "UPDATE analytics.scored.customer_reviews "
            "SET draft_reply = ? WHERE review_id = ?",
            params=[edited, int(selected)]
        ).collect()
        st.success("Updated.")
```

(The `UPDATE` is illustrative — in a real app you'd write to a
`triage_state` table, not the scored view, since the view is
recomputed.)

### Part 3 — Wire the secrets

Anything sensitive (PATs, S3 keys) goes in Snowflake secrets:

```sql
CREATE OR REPLACE SECRET my_s3_creds
  TYPE = PASSWORD
  USERNAME = 'AKIA...'
  PASSWORD = '...';
```

The app references secrets by name. No credentials in source.

### Part 4 — Schedule a refresh

The scored view re-derives on every query, which is fine for
demo-scale data. In production, swap it for a Task that
materializes a `customer_reviews_tbl` on a schedule:

```sql
CREATE OR REPLACE TASK refresh_scored
  WAREHOUSE = ai_demo_wh
  SCHEDULE = '60 MINUTE'
AS
  CREATE OR REPLACE TABLE analytics.scored.customer_reviews_tbl AS
  SELECT * FROM analytics.scored.customer_reviews;
```

### Part 5 — Try the app

Open the app URL from the Snowflake UI (`Projects → Streamlit →
review_triage`). The sidebar should populate, the search box
should hit Cortex Search, and the detail pane should let you
edit a draft reply.

## Key takeaways

- Cortex Search gives the app a fast retrieval layer; the scored
  view provides structured columns.
- The Streamlit app is a single file with `get_active_session()`,
  standard widgets, and a Cortex Search call.
- For production, materialize a scored *table* on a Task and
  read that in the app — the view is for demos.

## What's next

In **L100 — Hands-on: Clean Up** we drop the demo objects so
we don't keep paying for the Cortex Search service while we
focus on the next section.
