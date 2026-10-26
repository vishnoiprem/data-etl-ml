# Section 6 Quiz — Loading Unstructured Data

> 10 questions, multi-choice, single answer. Answers are hidden
> in collapsible blocks; expand only after you've attempted the
> question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** Which Snowflake data type is used to ingest semi-structured data (JSON, Parquet, Avro)?

- A. `STRING`
- B. `OBJECT`
- C. `VARIANT`
- D. `JSON`

<details><summary>Show answer</summary>

**C — `VARIANT`.** Snowflake uses a single universal type,
`VARIANT`, to hold any JSON-shaped value (object, array,
scalar, null). The other types are too narrow — a `STRING`
column can't be queried with the `:` operator.

</details>

---

**Q2.** In the two-step JSON pipeline, what is the role of the
`raw` table?

- A. The table BI tools query for analytics
- B. A safety-net landing pad that stores the original JSON plus
  filename/timestamp metadata
- C. The table used to share data with other Snowflake accounts
- D. The materialized view layer

<details><summary>Show answer</summary>

**B — A safety-net landing pad.** The `raw` table stores the
JSON as a `VARIANT` plus `METADATA$FILENAME`,
`METADATA$FILE_ROW_NUMBER`, and a `loaded_at` default. If the
downstream parsing is wrong, you re-run L49 against `raw` —
no S3 round-trip needed.

</details>

---

**Q3.** What does the `:` operator do in Snowflake?

- A. Casts a `VARIANT` to a typed value
- B. Reaches into a JSON path and returns a `VARIANT`
- C. Concatenates two strings
- D. Creates an index on a JSON field

<details><summary>Show answer</summary>

**B — Reaches into a JSON path.** `raw:customer.name` returns
a `VARIANT` containing the `name` field. Pair it with
`::STRING` (cast) to get a typed value: `raw:customer.name::STRING`.

</details>

---

**Q4.** Snowflake's array indexing is:

- A. One-based (`line_items[1]` is the first element)
- B. Zero-based (`line_items[0]` is the first element)
- C. Negative indexes are supported (`line_items[-1]` is the last)
- D. Both one- and zero-based are supported

<details><summary>Show answer</summary>

**B — Zero-based.** `line_items[0]` is the first element. This
matches C / Java / JS and is a common source of off-by-one
bugs for SQL Server / Oracle backgrounds. Negative indexing is
**not** supported.

</details>

---

**Q5.** What does `LATERAL FLATTEN(input => raw:line_items)`
do?

- A. Concatenates the array elements into a single string
- B. Returns the size of the array
- C. Turns one row with an array into N rows, one per element
- D. Removes duplicates from the array

<details><summary>Show answer</summary>

**C — Turns one row with an array into N rows.** `LATERAL`
allows the function to reference columns from the FROM clause.
Each element of `raw:line_items` becomes its own row, with the
order's scalar fields repeated on each. Output columns include
`value`, `seq`, `index`, `path`, and `key`.

</details>

---

**Q6.** What does `OUTER => TRUE` do in
`LATERAL FLATTEN(input => raw:line_items, OUTER => TRUE)`?

- A. Allows the array to be modified
- B. Keeps rows whose array is empty (LEFT JOIN semantics)
- C. Forces all output columns to be NOT NULL
- D. Includes a column with the array's outer type

<details><summary>Show answer</summary>

**B — Keeps rows whose array is empty.** Without `OUTER => TRUE`,
orders with `line_items = []` produce zero rows and **disappear**
from the result. With it, the order is preserved with `f.*`
columns all `NULL`.

</details>

---

**Q7.** A JSON path that doesn't exist in a row will produce:

- A. An error (`PATH_NOT_FOUND`)
- B. A `NULL` value (silent)
- C. The string `'MISSING'`
- D. An empty string

<details><summary>Show answer</summary>

**B — A `NULL` value, silently.** Snowflake does **not** raise
an error on missing JSON paths; it returns `NULL`. This is the
desired behaviour for the `raw` layer — bad rows are visible but
don't break the load.

</details>

---

**Q8.** Which file-format option should you use if every line in
the JSON file is a separate JSON object (`.jsonl` style)?

- A. `STRIP_OUTER_ARRAY = TRUE`
- B. `STRIP_OUTER_ARRAY = FALSE`
- C. `TYPE = JSON_LINES`
- D. `COMPRESSION = NONE`

<details><summary>Show answer</summary>

**B — `STRIP_OUTER_ARRAY = FALSE`.** This is the default and is
the right setting for "JSON Lines" files where each line is a
separate JSON object. Set it to `TRUE` only when the file is a
single big array like `[{…}, {…}]`.

</details>

---

**Q9.** What is the **watermark pattern** for incremental JSON
loads?

- A. `WHERE filename = '<last_loaded_file>'`
- B. `WHERE loaded_at > (SELECT MAX(loaded_at) FROM curated)`
- C. `WHERE ROW_NUMBER() OVER (ORDER BY loaded_at) <= 1000`
- D. `WHERE raw IS NOT NULL`

<details><summary>Show answer</summary>

**B — `WHERE loaded_at > (SELECT MAX(loaded_at) FROM curated)`.**
This inserts only rows that arrived after the last successful
curated insert, making the insert **idempotent** and safe to
re-run. It's the basis of every append-only JSON pipeline.

</details>

---

**Q10.** Why is the `raw` layer typically `CREATE OR REPLACE`
while the `curated` layer is `INSERT … SELECT`?

- A. CTAS is illegal on `VARIANT` tables
- B. `raw` is rebuildable from S3 cheaply; `curated` accumulates
  history and should be append-only
- C. CTAS can't reference JSON
- D. The two statements use different warehouses

<details><summary>Show answer</summary>

**B — `raw` is rebuildable from S3 cheaply; `curated`
accumulates history.** Replacing `raw` on each run lets you
change the JSON parser without re-ingesting from S3. The
curated table is the one downstream consumers read, so
`INSERT … SELECT` preserves history and avoids re-creating
expensive aggregations.

</details>