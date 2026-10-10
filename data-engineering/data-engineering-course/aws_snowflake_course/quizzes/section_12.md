# Section 12 Quiz — Cortex AI & Machine Learning

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** Which three AI SQL functions cover the bulk of text-AI
needs in Cortex?

- A. `SENTIMENT`, `SUMMARIZE`, `TRANSLATE`
- B. `ENCODE`, `DECODE`, `EMBED`
- C. `FORECAST`, `CLASSIFY`, `ANOMALY_DETECTION`
- D. `PARSE`, `SCAN`, `INDEX`

<details><summary>Show answer</summary>

**A — `SENTIMENT`, `SUMMARIZE`, `TRANSLATE`.** These three
return a value per row in a `SELECT`. Anything more exotic (a
custom prompt, structured JSON output) goes to `COMPLETE`.

</details>

---

**Q2.** Which Snowflake function is the generic LLM call you
use for custom prompts?

- A. `SNOWFLAKE.CORTEX.SENTIMENT`
- B. `SNOWFLAKE.CORTEX.COMPLETE`
- C. `SNOWFLAKE.CORTEX.RUN`
- D. `SNOWFLAKE.CORTEX.EXEC`

<details><summary>Show answer</summary>

**B — `SNOWFLAKE.CORTEX.COMPLETE`.** Takes a model name and a
chat-style message list, returns a JSON response you parse
yourself.

</details>

---

**Q3.** What does a Cortex Search service index, and how do
you query it?

- A. Numeric columns only; queried with `SELECT * FROM
  <svc>;`
- B. A text column of a table; queried with
  `SEARCH_PREVIEW` or a REST API
- C. JSON files in a stage; queried with `LIST`
- D. A view; queried with `SHOW VIEWS`

<details><summary>Show answer</summary>

**B — A text column, queried with `SEARCH_PREVIEW` (SQL) or a
REST API.** The service builds a hybrid keyword + vector index
on the column you specify and refreshes it on a `TARGET_LAG`
schedule.

</details>

---

**Q4.** What is the role of the **semantic model** in Cortex
Analyst?

- A. A trained neural network that lives inside the Snowflake
  warehouse
- B. A YAML file describing tables, columns, joins, and
  business terms that the text-to-SQL agent reasons over
- C. A copy of the LLM used to generate the response
- D. The OAuth scope of the REST API

<details><summary>Show answer</summary>

**B — A YAML semantic model.** It grounds the LLM's SQL
generation in *your* schema and lets you define synonyms and
pre-built filters. No semantic model → the agent has no
grounding and refuses to answer.

</details>

---

**Q5.** Which Cortex service is best for "let analysts ask
questions in plain English and get SQL back"?

- A. Cortex Search
- B. Cortex Analyst
- C. Snowflake ML
- D. Snowflake Notebooks

<details><summary>Show answer</summary>

**B — Cortex Analyst.** It is the text-to-SQL surface. Cortex
Search is for retrieval over a text column; Snowflake ML is for
forecasting and custom models.

</details>

---

**Q6.** Where does **Snowflake ML** training run?

- A. On a Snowflake-managed serverless GPU pool
- B. On your warehouse
- C. On a separate Snowpark container service cluster
- D. On your laptop

<details><summary>Show answer</summary>

**B — On your warehouse.** The other three Cortex surfaces
(AI SQL, Search, Analyst) are serverless; ML training is the
outlier. You size and pay for the warehouse.

</details>

---

**Q7.** Which Snowflake surface combines a Python notebook IDE
with a live Snowpark session?

- A. Worksheets
- B. Tasks
- C. Snowflake Notebooks
- D. Streamlit in Snowflake

<details><summary>Show answer</summary>

**C — Snowflake Notebooks.** Jupyter-compatible Python with
`get_active_session()` in the default cell, mixable SQL cells,
and the option to schedule the whole notebook as a Task.

</details>

---

**Q8.** When you open a Streamlit in Snowflake app, the
queries it runs execute under:

- A. A single service account, regardless of who opened the
  app
- B. The opener's role — so masking and row access policies
  apply
- C. `ACCOUNTADMIN` always
- D. The role that created the Streamlit object

<details><summary>Show answer</summary>

**B — The opener's role.** The app uses
`get_active_session()`, which inherits the credentials of the
user who opened the URL. RLS and masking work automatically.

</details>

---

**Q9.** Which Cortex function would you use to label the
content of an image attached to a row?

- A. `SNOWFLAKE.CORTEX.SENTIMENT`
- B. `SNOWFLAKE.CORTEX.PARSE_DOCUMENT`
- C. `SNOWFLAKE.CORTEX.CLASSIFY_IMAGE`
- D. `SNOWFLAKE.CORTEX.EMBED_TEXT_768`

<details><summary>Show answer</summary>

**C — `SNOWFLAKE.CORTEX.CLASSIFY_IMAGE`.** Takes an image URL
and a list of candidate labels, returns the best label +
confidence. `PARSE_DOCUMENT` is for text-on-document
extraction.

</details>

---

**Q10.** What is the **scored view** pattern, and why is it
useful?

- A. A view that ranks Cortex function results for
  performance
- B. A single view that materializes all Cortex function
  outputs as columns, so every downstream surface reads the
  same numbers
- C. A Snowpark UDF that scores query cost
- D. A Snowflake Marketplace listing of pre-built Cortex
  models

<details><summary>Show answer</summary>

**B — A single view that materializes Cortex outputs as
columns.** It is the contract the Streamlit app, the search
service, and any notebooks all read from. If the source schema
changes, you change the view once.

</details>
