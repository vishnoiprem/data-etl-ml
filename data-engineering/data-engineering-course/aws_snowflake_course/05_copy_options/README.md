# Section 5 — Copy Options

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L33–L40
> **Duration:** ~56 min

This section is the deep dive on the **`COPY INTO` command
options**. We cover **named file format objects** (the
production pattern), the **`ON_ERROR` recap** from L32,
**`VALIDATION_MODE`** for dry-run loads, **combining
options** (`PATTERN`, `PURGE`, `FORCE`), **working with
rejected records** via the `VALIDATE` table function,
**`SIZE_LIMIT`** for cost guards, **`RETURN_FAILED_ONLY`**
for cleaner diagnostic output, and **`TRUNCATECOLUMNS` +
`FORCE` + load history** as the section wrap-up.

By the end of this section you should be able to:
- Define and reuse **named file format objects** for
  production pipelines.
- **Dry-run** a `COPY INTO` with `VALIDATION_MODE` before
  committing.
- **Inspect and recover** from rejected records using
  `VALIDATE`.
- Apply **cost guards** with `SIZE_LIMIT` and `RETURN_FAILED_ONLY`.
- **Replay or re-load** with `FORCE = TRUE` safely.
- Read the **load history** to debug any production load.

| L# | Title | Min |
|---|---|---|
| L33 | File format object | 8:00 |
| L34 | Summary | 5:00 |
| L35 | VALIDATION_MODE | 8:00 |
| L36 | Using the copy options | 8:00 |
| L37 | Working with rejected records | 8:00 |
| L38 | SIZE_LIMIT | 6:00 |
| L39 | RETURN_FAILED_ONLY | 6:00 |
| L40 | TRUNCATECOLUMNS + FORCE + Load history | 7:00 |

## Key concepts you'll need later

- **Named file format objects** — production pattern;
  reusable across stages and tables.
- **`VALIDATION_MODE`** — dry-run a `COPY INTO`; catches
  errors before committing.
- **`VALIDATE` table function** — returns rejected records
  with reason and source location.
- **`SIZE_LIMIT`** — byte cap per `COPY INTO` statement.
- **`RETURN_FAILED_ONLY`** — filters the result to failed
  files only.
- **`TRUNCATECOLUMNS`** — silent string truncation; use
  sparingly.
- **`FORCE = TRUE`** — bypass load history; always combine
  with `TRUNCATE` or `MERGE`.
- **Load history** — 64-day default retention; archive to
  your own table for longer history.

## What comes next

Section 6 is **Loading Unstructured Data** — we move beyond
flat CSV/JSON to **semi-structured JSON with nested arrays
and objects**, and the **`LATERAL FLATTEN` pattern** for
unnesting. By L49 you'll be able to load and parse any
JSON shape into a relational model.