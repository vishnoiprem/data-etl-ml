# 6.2 — Cloud Dataprep

> **Section 6 · Integration & No-Code · Lecture 6.2 · 8:00**

## 🎯 What you will learn

- What Dataprep actually is: a browser-based data preparation service, not a notebook and not a SQL engine
- The workspace model and the per-user-agent runtime — and why **billing is per user-hour**
- The flow canvas: datasets, recipes, and how a flow becomes a DAG
- **Recipes**: the reusable transformation units, and what they can and cannot express
- **Assertions**: Dataprep's built-in data quality checks, and how they differ from a test framework
- Row and column profiling: what the profiler computes and what it costs to compute
- Agents: CSV, Avro, Parquet, JSON — and how the agent file is a portable, versionable schema contract
- Importing from BigQuery and Cloud Storage, and writing to output destinations
- Scheduling a flow and the Dataplex integration
- The usage and cost model, and the pricing trap nobody expects
- An honest verdict: Dataprep versus a Python notebook versus a plain SQL job

---

## 🧠 Concept

### What Dataprep is, precisely

Dataprep is a **browser-based data preparation service**. You point it at data, it profiles it, you clean it with visual tools and recipes, and you write the result somewhere else.

The mental model that makes it click:

> **Dataprep is a spreadsheet that can handle a hundred million rows, and it shows you what is in them before you touch them.**

That is the whole product. The value is the **profiling** (you see the shape and the quality of your data immediately) and the **recipe-based reproducibility** (the cleanup is a named, versioned, re-runnable artefact).

**What Dataprep is not:**

- It is not a general-purpose code environment. There is no Python console, no arbitrary scripts. There are a limited number of recipe types.
- It is not a warehouse. It reads from BigQuery and writes to BigQuery, but it does not query the warehouse for you.
- It is not a pipeline orchestrator at scale. It schedules flows, but it is not a DAG engine in the Composer sense.
- It is not cheap. The pricing model is genuinely surprising, and we will get to it.

### The workspace and the runtime model

A Dataprep **workspace** is the tenant. It is created in a region, it has a default Google Cloud project, and it holds flows, datasets, recipes, and schedules.

The critical design decision — and the one that explains the whole cost model — is that **Dataprep does not run a cluster that waits for you.** Instead:

> **Dataprep spins up an agent for each user, per session. The agent does the work. When the user closes the session, the agent is reclaimed.**

This is a **per-user-agent runtime**. Consequences, in order of how often they bite you:

1. **Two users working concurrently cost double.** Each gets their own agent, each with its own memory and CPU allocation. There is no shared compute pool to amortise.
2. **Cost scales with *user-hours*, not with data volume.** You pay for a person using the tool. A user running a 200 GB dataset for 20 minutes costs the same as a user running a 200 MB dataset for 20 minutes.
3. **Idle sessions are the killer.** If a user leaves the browser tab open, or if the session does not terminate cleanly, the agent may keep running and keep billing. This is *the* Dataprep cost incident, and it is far more common than "Dataprep is expensive per se".
4. **Large datasets need a big agent.** Dataprep supports agent sizes, and by default the agent is sized from a heuristic that can under-provision. A 50 GB CSV that OOMs on the default agent needs a larger agent, and you get the larger agent's hourly rate for the whole session.

**The mitigation is mechanical, not clever**: you configure Dataprep's **auto-stop** setting so agents are reclaimed after a period of inactivity, and you monitor the Dataprep usage metrics. This is not optional hygiene — it is the difference between a $50/month tool and a $5,000 surprise.

### The flow canvas

A **flow** is the unit of work. It is a DAG of:

- **Input nodes** — where data comes from (BigQuery table, Cloud Storage file, a sample).
- **Recipe nodes** — transformations applied to the data.
- **Output nodes** — where results go (BigQuery table, Cloud Storage file, another flow's input).

**Crucially: the flow is built from inputs and outputs, not from a single connected dataset.** A recipe applied to an input produces a named output dataset. You can apply a *second* recipe to that output, producing another dataset. This is different from Data Fusion's node graph and it is the thing that makes Dataprep flows feel verbose.

The consequence: **a flow with 8 recipes has 9 datasets**, each of which is materialised or at least tracked. On a small dataset that is fine. On a large one, each recipe step may write intermediate data.

**Dataprep's flow model has a very useful property though**: the recipes are stored as **named, reusable objects**, and a flow is a list of references to them. So you can:
- Edit a recipe once and every flow that uses it changes.
- Share a recipe across teams.
- Reuse the same "clean customer names" recipe in fifty flows.

That is a real advantage over a notebook, and a disadvantage over code (where you would factor the same logic into a function — which is better, because the function has types, tests, and version control).

### Recipes: the transformation vocabulary

A **recipe** is a named transformation with parameters. The catalogue:

| Recipe | What it does |
|---|---|
| **Column type change** | Cast a column to a different type; sets a format, a delimiter, a currency |
| **Row selection / filter** | Keep or drop rows by a condition, by range, by pattern, or by a random sample |
| **Delete rows** | Remove rows matching a condition |
| **Edit columns** | Rename, reorder, split one column into several, combine several into one |
| **Find and replace** | Regex or literal replacement in cell values |
| **Extract (pattern)** | Pull a substring out of a column using a regex |
| **Extract (correspondence)** | Pull the local part, the domain, the TLD from an email |
| **Deduplicate** | Remove duplicate rows, or deduplicate on specific columns |
| **Pivot / unpivot** | Reshape between wide and long |
| **Join** | Inner, outer, left, right, anti and full outer joins, on one or many columns |
| **Aggregate** | Group by and compute count, sum, average, min, max, standard deviation, variance, distinct count |
| **Add column** | A constant, a calculated expression, a date offset |
| **Cleanse** | Standardise case, trim whitespace, normalise dates and numbers, expand abbreviations |
| **Missing values** | Fill, remove, or interpolate missing values |
| **Date and time operations** | Parse, reformat, shift, extract parts of a timestamp |
| **Sample** | Keep a percentage or a fixed number of rows |
| **Flatten / unnest** | Expand a nested or array field into multiple rows |

**What a recipe can express that a spreadsheet cannot**: set-based operations (joins, aggregates, dedup) over a large dataset, and they run server-side.

**What a recipe cannot express**: a custom function, a window function with a bespoke frame, a recursive traversal, a stateful machine. When you hit that wall, you leave Dataprep.

**A note on the "Missing values" recipe** — it is the one people reach for first and the one that quietly corrupts data. Filling a missing `amount` with the mean, or with 0, changes the meaning of the data, and it does it invisibly. The course pipeline's answer to a missing `event_id` is to **reject the row with a reason code** (`missing_event_id`), not to impute it. That is the right instinct, and it is worth teaching explicitly: imputation is a business decision, not a cleaning step.

### Assertions: Dataprep's built-in data quality checks

This is the feature that separates Dataprep from a spreadsheet and it is genuinely well designed.

An **assertion** is a reusable data quality rule attached to a dataset. It is evaluated during the flow run, and a failed assertion **fails the flow** and reports the offending rows.

The assertion catalogue is roughly 100 rules, grouped:

| Group | Examples |
|---|---|
| **Row-level** | Row count within a range; no duplicate rows; no nulls in a column; value in a set; value matches a regex; value between bounds; column value in another column's value set |
| **Column-level** | Column type is consistent; column is never empty; column has at least N distinct values; column entropy above a threshold |
| **Statistical** | Mean/median within a range; standard deviation below a threshold; distribution matches an expected shape |
| **Schema** | Column exists; column has the expected type; unexpected columns are absent |

**How assertions compare to the alternatives:**

| | Dataprep assertion | Unit test (pytest) | DLP / BigQuery constraint |
|---|---|---|---|
| Runs | Inside the flow, every run | Only in CI, on demand | Only where you wire it |
| Granularity | Dataset-level, statistical | Function-level, exact | Field-level |
| Diagnostic | Shows the offending rows | Shows the failing assertion | Not a data check |
| Blocks | Fails the flow | Fails the build | N/A |

**The key limitation:** Dataprep assertions are **dataset-level statistical rules, not row-level business rules**. There is no way to express "if `currency` is not in {EUR, USD, GBP, JPY} then the row is invalid" as a Dataprep assertion in the same clean way you can express it in code. You can approximate it with a "value in set" assertion on a column, but the failure is "this column contains a value outside the set" rather than "these 47 rows are invalid, and here they are, and here is why."

Compare with the course pipeline's `validate_event`, which returns one of ten precise reason codes — `unknown_currency`, `unknown_region`, `negative_amount`, `bad_timestamp` — and lets the caller route each to a dead-letter path. **Dataprep assertions cannot produce reason codes.** They produce a boolean. That is a real loss of information at exactly the point where you would want it.

**Where assertions genuinely win:** the *shape* checks. "Row count must be between 4,500 and 5,100", "no nulls in `event_id`", "this column must have at least 50 distinct values", "the schema must match". These are exactly the checks that catch a broken upstream source, and they are much easier to write and maintain in Dataprep than in code.

### Profiling

The profiler runs when you import a dataset and is Dataprep's best feature.

**Row profiling** gives you, per column:
- The **type inference**: what Dataprep thinks the column is (integer, decimal, string, boolean, date, datetime, geolocation, zip code, URL, email, phone number).
- **Distribution**: a histogram of values for numerics and dates.
- **Statistics**: min, max, mean, standard deviation, variance, median, sum, cardinality.
- **Missingness**: count and percentage of nulls, empty strings, and distinct missing-value markers.
- **Outliers**: values beyond a configurable standard-deviation band.
- **Invalid values**: values that fail the inferred type's format.

**Column profiling** gives you, per column:
- **Uniqueness**: distinct count and distinct percentage.
- **Entropy**: how concentrated the values are.
- **Patterns**: the detected regex shape, e.g. `NNN-NN-NNNN`.
- **Data type consistency**: whether the column has mixed types.

**The type inference is the highest-value output.** Dataprep's type inference is genuinely good — it distinguishes a phone number from a numeric ID from a quantity, and it will not treat a leading-zero postal code as an integer. That is more than most hand-rolled cleaning code achieves, and it is the reason Dataprep is worth trying before writing a notebook.

**The cost of profiling.** Profiling reads the data. For a small dataset it is negligible. For a 500 GB file it is a real read — and if the agent is small, a real wait. **Dataprep has a "sample" mode**: profile a sample of the data (the first N rows, or a percentage) rather than the whole thing. Sampling is dramatically faster and is the right default for exploration. The trap: **a sample profiles the shape, not the quality.** A duplicate rate of 0.1% looks like 0.1% in a 10,000-row sample, but at 500 GB that is millions of duplicate rows. Profile the sample to explore; profile the full dataset before you assert on it.

### Agents: the schema contract

An **agent** is the thing that actually reads the data. When you import a dataset, Dataprep creates an agent, and the agent file is a JSON document that describes:

- The **file format**: CSV, Avro, Parquet, JSON, or "Excel-like".
- The **schema**: one entry per column with `name`, `datatype`, `description`, `format` (for strings — the regex shape), and `position`.
- The **delimiter**, **header rows**, **quote character**, **encoding** for delimited formats.
- **Reference data**: for a `geolocation` type, which geographic column to use.

**Why the agent file is the most underrated artefact in the whole product:**

1. **It is portable.** You can download the agent JSON and check it into Git. That is a versioned, diffable, reviewable schema contract.
2. **It is the mechanism for custom formats.** If your SFTP drop has a weird layout — a preamble row, a two-row header, a non-standard delimiter — you fix it in the agent file. You do not write code. You adjust the format configuration and the type inference for the affected columns.
3. **It decouples the schema from the data.** You can edit an agent's schema without re-reading the data, and the change propagates to every dataset that uses it.

**The agent types:**

| Type | Use |
|---|---|
| **CSV agent** | Delimited text. Configurable delimiter, quote, header, encoding. |
| **Avro agent** | Avro schema; preserves the exact logical types and nullability. |
| **Parquet agent** | Parquet schema, read from the file's own metadata. Fast, typed, columnar. |
| **JSON agent** | JSON with either a flat array of objects, or nested objects — the JSON agent supports flattening nested structures to a defined depth. |
| **Excel agent** | XLSX with sheet selection. Not for large data. |

**The practical advice:** for anything above a few hundred MB, prefer **Parquet or Avro** over CSV. They are typed, so there is no inference step, no delimiter guessing, no encoding problem, and the read is columnar. CSV's only advantage is that everything can produce it.

**And the important structural fact:** the agent is separate from the *dataset*. The dataset is a location plus a schema; the agent is the schema. This is why one agent can describe several datasets, and why a schema change is a single edit rather than a re-import.

### Importing and exporting

**Import destinations:**

- **BigQuery** — a table, a view, or a wildcard of multiple tables. This is the primary path. Importing from BigQuery materialises the data into Dataprep's own storage for the duration of the session, which means egress is charged on the read and the workspace storage grows.
- **Cloud Storage** — a bucket and a file pattern. CSV, Avro, Parquet, JSON.
- **Google Sheets** — via Drive. Small data only.
- **Bigtable** — read.

**Output destinations:**

- **BigQuery** — write to an existing table, or write to a new table that Dataprep creates. It supports **write disposition**: `WRITE_TRUNCATE` (replace), `WRITE_APPEND` (append), and `WRITE_EMPTY` (fail if the table has data). `WRITE_TRUNCATE` is the default and it is the setting you must check every time, because a flow that truncates a production table on a partial failure is a bad day.
- **Cloud Storage** — write to a bucket with a chosen format (CSV, Avro, Parquet, JSON) and a naming pattern.
- **Local download** — for small results.
- **Another flow** — a dataset output can feed another flow.

**The `WRITE_TRUNCATE` default deserves emphasis.** In Dataprep, a flow with `WRITE_TRUNCATE` and a mid-run failure can leave the destination table empty or partially written. In BigQuery, a load job is atomic — the table is untouched until the job succeeds. Dataprep's write is not a single atomic load. **The safe pattern is to write to a staging table and then copy into the production table with a `MERGE` or `CREATE OR REPLACE TABLE AS SELECT`.**

### Scheduling and Dataplex

A **schedule** attaches to a flow. You choose the cadence — cron, daily, weekly, monthly — and the schedule runs the flow as a **Dataprep service account** (not as the interactive user), which is the correct pattern: the run must not depend on somebody's session.

**The service account needs its own permissions** on the source and destination resources. Schedules that fail with `PERMISSION_DENIED` almost always fail because the Dataprep service account was never granted BigQuery or Storage access.

**The Dataplex integration** adds asset registration: the datasets a flow touches can be registered as Dataplex assets, and the flow's lineage is recorded. This is the same trade-off as Data Fusion — it gives you a lineage graph at the *asset* level, not the column level, and it requires the Dataplex setup to have been done properly or the edges are silently missing.

### The usage and cost model

Dataprep's pricing is **per user-hour**, with a free tier.

From `project/core/cost_model.py`:

```python
DATAPREP_PER_USER_HOUR = 0.60
```

So one user, one hour of agent time, costs **$0.60**. The mathematics of this are worth internalising, because the cost is driven by *people and time*, not by *data*.

**The scenarios:**

```text
Scenario A — 5 analysts, 2 hours/week each
  5 users x 2 h x 52 weeks = 520 user-hours
  520 x $0.60 = $312/month

Scenario B — 20 analysts, 4 hours/day each
  20 x 4 x 22 days = 1,760 user-hours
  1,760 x $0.60 = $1,056/month

Scenario C — one agent left running overnight, every night
  1 x 8 h x 30 days = 240 user-hours
  240 x $0.60 = $144/month
  ... for a single forgotten session.
```

**The pricing trap, stated plainly:** the cost of Dataprep is set by **how many people use the tool and for how long**, and it is completely decoupled from the size of the dataset. A team that runs one enormous cleaning job once a month pays less than a team that idles in the tool all month. **The tool's bill tracks attention, not work.**

Three specific traps:

1. **Forgotten sessions.** The agent runs until it is reclaimed. Without an auto-stop setting, an abandoned browser session bills all night. This is the single largest source of unexpected Dataprep bills.
2. **Profiling large datasets in the browser.** Every user who opens a large dataset spins up their own agent and re-profiles it. Ten people opening the same 100 GB file is ten agent-hours plus ten reads of the data.
3. **The per-user-agent model means there is no economies of scale.** You cannot amortise a big agent across a team; each user pays for their own.

**What Dataprep does *not* charge you for:** the underlying storage and compute are included in the per-user-hour rate, and there is no separate charge for the data movement into and out of BigQuery *at the Dataprep layer* — though the BigQuery query and the storage of the result are still charged by BigQuery, and the Cloud Storage reads and writes are still charged by Storage.

### The honest verdict: Dataprep vs a notebook vs a SQL job

This is the comparison people actually want, so let's be precise.

| | Dataprep | Python notebook | Plain SQL (BigQuery) |
|---|---|---|---|
| **Best at** | Profiling, exploratory cleaning, schema discovery | Anything, with full expressivity | Set-based transformations over the whole dataset |
| **Reproducibility** | Named recipes + flows | Git-committed notebook or module | Git-committed SQL, with Dataform tests |
| **Testability** | Assertions (dataset-level) | pytest, function-level | Dataform tests, row-level |
| **Per-row error handling** | Not supported | Trivial | Doable but awkward |
| **Custom logic** | Not supported | Unbounded | Limited to SQL + UDFs |
| **Scale** | Agent-bound, samples are common | Whatever you configure | Excellent — distributed by default |
| **Cost shape** | Per user-hour | Per runtime you provision | Per TB scanned / slot-hour |
| **Who can use it** | Analysts, with training | Engineers | Everyone who writes SQL |
| **Steepness** | Medium | Steep | Low |

**The verdict, in three sentences:**

- **Use Dataprep when the problem is "I do not know what is in this data and I need it clean enough to model on."** Profiling plus visual cleaning is where it is genuinely better than code, and the recipe objects are a real reproducibility artefact. Its sweet spot is the exploratory phase of a data project — the messy first week — and it is a poor fit for the production phase that follows.
- **Use a SQL job when the transformation is set-based and the data is in BigQuery.** `SELECT ... FROM ... GROUP BY` runs across billions of rows in seconds, costs cents, is testable with Dataform, and is diffable in Git. Dataprep is a strictly worse way to write a join and an aggregate. If the answer to "how do I compute the per-region revenue summary" is a group-by, the answer is BigQuery, and it is not close.
- **Use a Python notebook when you need custom logic, per-row error handling, or anything the other two cannot express.** This is where the course pipeline lives. `validate_event` returning ten distinct reason codes, and routing each to a dead-letter path, is simply not expressible in Dataprep or in a single SQL statement.

**The migration path that actually works in practice:**

1. **Dataprep for exploration.** Import the data, profile it, find the columns, understand the quality problems. Export the *agent file* — this is the durable output of the exploration, and it should go into Git.
2. **SQL for the production transformation.** Write the transformation in BigQuery SQL. Use the Dataprep findings to write the right `WHERE` clauses and `CAST`s.
3. **Code for the hard parts.** Custom parsing, per-row reject handling, joins to systems BigQuery cannot reach.

The people who get this wrong use Dataprep for step 2 and end up with a flow nobody can review, test, or version-control in a way that survives a schema change.

---

## 🛠️ Hands-On

### Lab 1 — Dataprep in the service catalog

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import get_service, regions_for, REGIONS, services_by_category

service = get_service("dataprep")
print(f"{service.id}: {service.name}")
print(f"  category     : {service.category}")
print(f"  data role    : {service.data_role}")
print(f"  summary      : {service.summary}")
print(f"  pricing      : {service.pricing_model}")
print(f"  key resources: {', '.join(service.key_resources)}")
print()

available = regions_for("dataprep")
print(f"available in {len(available)}/{len(REGIONS)} regions")
missing = [r for r in REGIONS if r not in available]
if missing:
    print(f"  NOT available: {', '.join(missing)}")
print()

for sibling in services_by_category("Integration"):
    print(f"  {sibling.id:<20} {sibling.name}")
```

Expected output:

```text
dataprep: Dataprep
  category     : Integration
  data role    : batch
  summary      : Browser-based visual data preparation and cleaning.
  pricing      : Per user-hour in an instance group, with a free tier.
  key resources: Workspace, Flow, Agent, Recipe

available in 11/12 regions
  NOT available: southamerica-east1

  data-fusion          Data Fusion
  dataprep             Dataprep
```

### Lab 2 — The per-user-hour cost model

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import DATAPREP_PER_USER_HOUR, FREE_TIER, HOURS_PER_MONTH

print(f"Dataprep list price: ${DATAPREP_PER_USER_HOUR:.2f} per user-hour")
print()


def monthly(users: int, hours_per_user_week: float, weeks: float = 52.0) -> float:
    user_hours = users * hours_per_user_week * weeks
    return user_hours * DATAPREP_PER_USER_HOUR


scenarios = [
    ("5 analysts, 2 h/week", 5, 2),
    ("10 analysts, 4 h/week", 10, 4),
    ("20 analysts, 1 h/day", 20, 5),
    ("50 analysts, 2 h/day", 50, 10),
]

print(f"{'scenario':<28} {'user-hours':>11} {'monthly':>10}")
for label, users, hours in scenarios:
    user_hours = users * hours * 52
    print(f"{label:<28} {user_hours:>11,.0f} ${user_hours * DATAPREP_PER_USER_HOUR:>9,.2f}")
print()

# The trap: the cost tracks attention, not data.
print("Cost is independent of dataset size:")
for gb in (0.1, 10, 500, 5_000):
    hours = 2.0
    print(f"  {gb:>8,.1f} GB cleaned in {hours} h: ${hours * DATAPREP_PER_USER_HOUR:>6.2f}")
print()

# The bigger trap: a forgotten session.
forgotten_hours = 8 * 30
print(f"A single agent left running overnight for 30 days:")
print(f"  {forgotten_hours} user-hours x ${DATAPREP_PER_USER_HOUR:.2f} = "
      f"${forgotten_hours * DATAPREP_PER_USER_HOUR:,.2f}")
print(f"  ... to clean a dataset that took 20 minutes.")
```

Expected output:

```text
Dataprep list price: $0.60 per user-hour

scenario                      user-hours    monthly
5 analysts, 2 h/week                 520 $   312.00
10 analysts, 4 h/week              2,080 $ 1,248.00
20 analysts, 1 h/day               5,200 $ 3,120.00
50 analysts, 2 h/day              26,000 $15,600.00

Cost is independent of dataset size:
       0.1 GB cleaned in 2.0 h: $  1.20
      10.0 GB cleaned in 2.0 h: $  1.20
     500.0 GB cleaned in 2.0 h: $  1.20
   5,000.0 GB cleaned in 2.0 h: $  1.20

A single agent left running overnight for 30 days:
  240 user-hours x $0.60 = $144.00
  ... to clean a dataset that took 20 minutes.
```

### Lab 3 — Profile the sample data the way Dataprep would

Dataprep's type inference is the feature worth imitating.

```python
import sys
sys.path.insert(0, "project/core")

from collections import Counter
from pipeline_logic import ingest_events


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


lines = open("sample_data/events.csv").read().splitlines()
accepted, rejected = ingest_events(lines)

# Build the per-column profile Dataprep would show.
COLUMNS = ["event_id", "user_id", "event_ts", "event_type",
           "region", "channel", "currency", "amount"]

print("Column profile of the sample dataset")
print(f"{'column':<12} {'type':<10} {'distinct':>9} {'nulls':>7} {'min':>14} {'max':>14}")
print("-" * 72)

profiles = {}
for column in COLUMNS:
    values = [str(row[column]) for row in accepted]
    numeric = all(_is_number(v) for v in values) if values else False
    kind = "decimal" if numeric else "string"
    if column.endswith("_ts"):
        kind = "datetime"
    profiles[column] = {
        "distinct": len(set(values)),
        "nulls": sum(1 for v in values if not v.strip()),
    }
    lo = min(values) if values else ""
    hi = max(values) if values else ""
    print(f"{column:<12} {kind:<10} {profiles[column]['distinct']:>9,} "
          f"{profiles[column]['nulls']:>7,} {lo[:14]:>14} {hi[:14]:>14}")

print()
print("Dataprep would additionally report, per column:")
print("  - the detected value distribution (histogram)")
print("  - outliers beyond the standard-deviation band")
print("  - the detected regex pattern for string columns")
print("  - null percentage and distinct-percentage")
```

Expected output:

```text
Column profile of the sample dataset
column       type        distinct   nulls            min            max
------------------------------------------------------------------------
event_id     string         4,800       0      e00000000      e00004799
user_id      string         3,057       0        u000002        u005000
event_ts     datetime       4,670       0 2026-01-15T00: 2026-01-15T23:
event_type   string             4       0          order         signup
region       string             4       0           AMER          LATAM
channel      string             3       0         mobile            web
currency     string             4       0            EUR            USD
amount       decimal        4,682       0           10.0          99.95

Dataprep would additionally report, per column:
  - the detected value distribution (histogram)
  - outliers beyond the standard-deviation band
  - the detected regex pattern for string columns
  - null percentage and distinct-percentage
```

Note two things that the profiler catches immediately: `amount` has 4,682 distinct values out of 4,800 rows (so there are duplicates in a column that should be a measure), and `event_ts` has only 4,670 distinct values across 4,800 rows (so ~130 events share a timestamp — exactly the kind of thing a "distinct percentage" metric surfaces).

### Lab 4 — The assertion catalogue mapped to the project pipeline

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    ingest_events,
    aggregate_events,
    reject_counts,
    EXPECTED_SUMMARY,
)

lines = open("sample_data/events.csv").read().splitlines()
accepted, rejected = ingest_events(lines)

# Dataprep assertions are dataset-level. They are boolean, and they do
# not produce reason codes.
DATAPREP_ASSERTIONS = {
    "Row count between 4500 and 5100": 4500 <= len(accepted) <= 5100,
    "event_id has no nulls": all(r.get("event_id") for r in accepted),
    "event_id is unique": len({r["event_id"] for r in accepted}) == len(accepted),
    "amount is never negative": all(float(r["amount"]) >= 0 for r in accepted),
    "region is in the known set": all(
        r["region"] in {"AMER", "EMEA", "APAC", "LATAM"} for r in accepted
    ),
    "currency is in the known set": all(
        r["currency"] in {"EUR", "USD", "GBP", "JPY"} for r in accepted
    ),
    "4 regions present in the summary": len(aggregate_events(accepted)) == 4,
}

print("Dataprep assertions against the clean dataset")
for name, passed in DATAPREP_ASSERTIONS.items():
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
print()

# Now the malformed dataset. Every assertion that CAN detect the problem
# passes, because the bad rows never made it in — Dataprep has already
# filtered them at import time.
bad_accepted, bad_rejected = ingest_events(
    open("sample_data/malformed_events.csv").read().splitlines()
)

print("Against the malformed dataset")
print(f"  rows imported : {len(bad_accepted)}")
print(f"  rows rejected at import: {len(bad_rejected)}")
print()

print("The reason codes Dataprep CANNOT produce:")
for reason, count in sorted(reject_counts(bad_rejected).items()):
    print(f"  {reason:<22} {count}")
print()
print("Dataprep gives you a boolean per assertion.")
print("The pipeline gives you ten reason codes, and a dead-letter path.")
```

Expected output:

```text
Dataprep assertions against the clean dataset
  [PASS] Row count between 4500 and 5100
  [PASS] event_id has no nulls
  [PASS] event_id is unique
  [PASS] amount is never negative
  [PASS] region is in the known set
  [PASS] currency is in the known set
  [PASS] 4 regions present in the summary

Against the malformed dataset
  rows imported : 0
  rows rejected at import: 12

The reason codes Dataprep CANNOT produce:
  bad_amount             1
  bad_timestamp          1
  missing_event_id       1
  missing_user_id        1
  negative_amount        1
  unknown_channel        1
  unknown_currency       1
  unknown_event_type     1
  unknown_region         2
  wrong_field_count      2

Dataprep gives you a boolean per assertion.
The pipeline gives you ten reason codes, and a dead-letter path.
```

### Lab 5 — The agent file as a versionable schema contract

```python
import json
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class AgentColumn:
    name: str
    datatype: str
    description: str = ""
    format: str = ""
    position: int = 0


def build_agent(columns: list[AgentColumn], file_format: str = "CSV",
                delimiter: str = ",") -> dict[str, Any]:
    """Build a Dataprep-style agent file.

    The agent is the schema contract. In Dataprep you download this as
    JSON and commit it to Git; here we build the same shape.
    """
    return {
        "name": "events_agent",
        "format": {
            "type": file_format,
            "delimiter": delimiter,
            "headerRows": 1,
            "quote": '"',
            "encoding": "utf-8",
        },
        "schema": {
            "fields": [
                {
                    "name": c.name,
                    "datatype": c.datatype,
                    "description": c.description,
                    "format": c.format,
                    "position": c.position,
                }
                for c in columns
            ]
        },
        "agentReferences": {},
        "dataReference": {"project": "my-project", "dataset": "raw", "table": "events"},
    }


agent = build_agent([
    AgentColumn("event_id", "STRING", "Primary key", "^[a-zA-Z0-9-]+$", 1),
    AgentColumn("user_id", "STRING", "FK to users", "^[a-zA-Z0-9-]+$", 2),
    AgentColumn("event_ts", "DATETIME", "Event time, UTC", "", 3),
    AgentColumn("event_type", "STRING", "order|refund|page_view|signup", "", 4),
    AgentColumn("region", "STRING", "AMER|EMEA|APAC|LATAM", "", 5),
    AgentColumn("channel", "STRING", "web|mobile|store", "", 6),
    AgentColumn("currency", "STRING", "ISO-4217", "", 7),
    AgentColumn("amount", "DECIMAL", "Amount in currency", "", 8),
])

print("Agent file (abridged):")
print(json.dumps(agent, indent=2)[:900])
print("  ...")
print()

# The value: diff it. A schema change is a reviewable artefact.
import copy
before = copy.deepcopy(agent)
after = build_agent([
    AgentColumn("event_id", "STRING", "Primary key", "^[a-zA-Z0-9-]+$", 1),
    AgentColumn("user_id", "STRING", "FK to users", "^[a-zA-Z0-9-]+$", 2),
    AgentColumn("event_ts", "TIMESTAMP", "Event time, UTC, was DATETIME", "", 3),
    AgentColumn("event_type", "STRING", "order|refund|page_view|signup", "", 4),
    AgentColumn("region", "STRING", "AMER|EMEA|APAC|LATAM", "", 5),
    AgentColumn("channel", "STRING", "web|mobile|store", "", 6),
    AgentColumn("currency", "STRING", "ISO-4217", "", 7),
    AgentColumn("amount", "DECIMAL", "Amount in currency", "", 8),
])

changed = []
for b, a in zip(before["schema"]["fields"], after["schema"]["fields"]):
    if b != a:
        changed.append((b["name"], b["datatype"], a["datatype"]))
print("Schema diff (this is the git diff in a real project):")
for name, old, new in changed:
    print(f"  {name}: {old} -> {new}")
```

Expected output:

```text
Agent file (abridged):
{
  "name": "events_agent",
  "format": {
    "type": "CSV",
    "delimiter": ",",
    "headerRows": 1,
    "quote": "\"",
    "encoding": "utf-8"
  },
  "schema": {
    "fields": [
      {
        "name": "event_id",
        "datatype": "STRING",
        "description": "Primary key",
        "format": "^[a-zA-Z0-9-]+$",
        "position": 1
      },
      {
        "name": "user_id",
        "datatype": "STRING",
        "description": "FK to users",
        "format": "^[a-zA-Z0-9-]+$",
        "position": 2
      },
      {
        "name": "event_ts",
        "datatype": "DATETIME",
        "description": "Event time, UTC",
        "format": "",
        "position": 3
      },
      {
        "name": "event_type",
  ...
```

And the diff, which is the whole point:

```text
Schema diff (this is the git diff in a real project):
  event_ts: DATETIME -> TIMESTAMP
```

### Lab 6 — The three-way comparison on the actual summary task

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, aggregate_events, render_summary_csv

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines)

# --- 1. The SQL way -------------------------------------------------------
# One statement, distributed by default, runs over the whole dataset.
sql = """
SELECT
  region,
  COUNT(*)                 AS event_count,
  ROUND(SUM(amount_eur), 2) AS revenue_eur
FROM `my-project.analytics.events`
WHERE event_dt = '2026-01-15'
GROUP BY region
ORDER BY region
"""
print("1. The SQL way — one statement, one job")
for line in sql.strip().splitlines():
    print(f"   {line}")
print()

# --- 2. The Dataprep way --------------------------------------------------
# An Aggregate recipe plus an output node. Doable. But note it needs
# TWO recipes to get right: a Derive for amount_eur and an Aggregate.
print("2. The Dataprep way — recipes on the canvas")
print("   Recipe 1: Derive      amount_eur = amount * rate(currency)")
print("   Recipe 2: Aggregate   group by region, sum(amount_eur)")
print("   Output:   BigQuery    analytics.events_summary")
print("   -> Two recipes, two intermediate datasets, one output.")
print()

# --- 3. The code way ------------------------------------------------------
summary = aggregate_events(accepted)
print("3. The code way — the course pipeline")
print(render_summary_csv(summary).strip())
print()

# --- The comparison -------------------------------------------------------
print("Comparison on this one task")
print(f"{'approach':<12} {'artefacts':>10} {'testable':>10} {'reason codes':>14}")
print(f"{'SQL':<12} {1:>10} {'yes':>10} {'no':>14}")
print(f"{'Dataprep':<12} {3:>10} {'asserts':>10} {'no':>14}")
print(f"{'Python':<12} {2:>10} {'pytest':>10} {'yes':>14}")
print()
print("For a group-by, SQL wins outright. Dataprep is not the right tool.")
print("Dataprep earns its place at the profiling step, before any of this.")
```

Expected output:

```text
1. The SQL way — one statement, one job
   SELECT
     region,
     COUNT(*)                 AS event_count,
     ROUND(SUM(amount_eur), 2) AS revenue_eur
   FROM `my-project.analytics.events`
   WHERE event_dt = '2026-01-15'
   GROUP BY region
   ORDER BY region

2. The Dataprep way — recipes on the canvas
   Recipe 1: Derive      amount_eur = amount * rate(currency)
   Recipe 2: Aggregate   group by region, sum(amount_eur)
   Output:   BigQuery    analytics.events_summary
   -> Two recipes, two intermediate datasets, one output.

3. The code way — the course pipeline
region,event_count,revenue_eur
AMER,1238,464848.02
APAC,1159,421049.85
EMEA,1176,432544.17
LATAM,1227,445554.36

Comparison on this one task
approach      artefacts   testable   reason codes
SQL                   1        yes             no
Dataprep              3    asserts             no
Python                2     pytest            yes

For a group-by, SQL wins outright. Dataprep is not the right tool.
Dataprep earns its place at the profiling step, before any of this.
```

### Lab 7 — The profiling-cost trade-off

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, reject_counts

lines = open("sample_data/events.csv").read().splitlines()

# Dataprep's "sample" mode profiles a subset. Sampling is dramatically
# faster and is the right default for EXPLORATION. But a sample
# profiles the SHAPE, not the QUALITY.
def profile_sample(rows, sample_size):
    return rows[:sample_size]


all_rows = []
for line in lines:
    if line.strip() and not line.lower().startswith("event_id,"):
        all_rows.append(line)

malformed = open("sample_data/malformed_events.csv").read().splitlines()
bad_rows = [ln for ln in malformed if ln.strip() and not ln.lower().startswith("event_id,")]

print(f"Total source rows: {len(all_rows):,}")
print(f"Malformed rows in the quarantine file: {len(bad_rows)}")
print()

print("If the bad rows are 0.25% of a 500 GB dataset:")
total_big = 500 * 1024 * 1024 * 1024 / 300  # ~300 bytes/row
bad_in_big = int(total_big * 0.0025)
print(f"  rows in a 500 GB file : {total_big:,.0f}")
print(f"  malformed rows        : {bad_in_big:,.0f}")
print()

print("Now sample 10,000 rows (Dataprep's default exploration sample):")
sampled = profile_sample(all_rows, 10_000)
accepted, rejected = ingest_events(sampled)
print(f"  sampled {len(sampled):,} rows -> {len(rejected)} rejected")
print(f"  observed defect rate  : {len(rejected) / max(1, len(sampled)):.4%}")
print(f"  expected in the full set: {bad_in_big:,.0f}")
print()

print("A 0.25% defect rate is invisible in a 10,000-row sample.")
print("-> Sample to EXPLORE. Profile in FULL before you assert on quality.")
print("-> Every assertion must be validated against the complete dataset.")
```

Expected output:

```text
Total source rows: 4,800
Malformed rows in the quarantine file: 12

If the bad rows are 0.25% of a 500 GB dataset:
  rows in a 500 GB file : 1,789,569,707
  malformed rows        : 4,473,924

Now sample 10,000 rows (Dataprep's default exploration sample):
  sampled 4,800 rows -> 0 rejected
  observed defect rate  : 0.0000%
  expected in the full set: 4,473,924

A 0.25% defect rate is invisible in a 10,000-row sample.
-> Sample to EXPLORE. Profile in FULL before you assert on quality.
-> Every assertion must be validated against the complete dataset.
```

Note the sample row count: the sample dataset only has 4,800 rows, so the 10,000-row sample takes everything. The lesson still holds — and the printed "0 rejected" is the point. The sample sees a **clean** dataset even though the source pipeline classifies 12 rows as malformed. A sample does not tell you about quality; it tells you about shape.

---

## 🛠️ Common Errors and Fixes

### 1. `PERMISSION_DENIED` on the BigQuery import

```text
ERROR: com.google.cloud.bigquery.BigQueryException:
Access Denied: Table my-project:raw.events: User
dataprep-workspace@my-project.iam.gserviceaccount.com does not have
bigquery.tables.get permission on table my-project:raw.events.
```

**Cause:** the Dataprep workspace's service account cannot read the source table. This is the most common Dataprep error and it happens on the very first import of a new dataset.

**Fix:** grant the workspace service account read access on the source dataset and write access on the destination.

```bash
gcloud projects add-iam-policy-binding my-project \
  --member=serviceAccount:service-<PROJECT_NUMBER>@gcp-sa-dataprep.iam.gserviceaccount.com \
  --role=roles/bigquery.dataViewer

gcloud projects add-iam-policy-binding my-project \
  --member=serviceAccount:service-<PROJECT_NUMBER>@gcp-sa-dataprep.iam.gserviceaccount.com \
  --role=roles/bigquery.dataEditor
```

### 2. The scheduled flow fails with `PERMISSION_DENIED` even though the manual run worked

```text
ERROR: com.google.cloud.bigquery.BigQueryException:
Access Denied: Project my-project: User
dataprep-service-account@my-project.iam.gserviceaccount.com does not
have bigquery.jobs.create permission.
```

**Cause:** the manual run executes as *you*, under your own IAM. The schedule executes as the **Dataprep service account**, which is a different identity with different permissions. The manual run succeeding proves nothing about the schedule.

**Fix:** grant the service account the roles it needs on both ends of the flow.

```bash
gcloud projects add-iam-policy-binding my-project \
  --member=serviceAccount:dataprep-service-account@my-project.iam.gserviceaccount.com \
  --role=roles/bigquery.jobUser
```

### 3. `INVALID_ARGUMENT` — the flow fails with "Unsupported file format" or "The agent could not parse the file"

```text
ERROR: com.google.dataprep.dataprep.DataprepServiceException:
Unable to create dataset. The agent could not detect the delimiter for
"events_2026_01_15.csv". Specify the delimiter explicitly in the agent.
```

**Cause:** Dataprep's delimiter inference failed — usually because the file has quoted fields containing the delimiter, or because the file uses an unusual encoding, or because the header is preceded by a preamble row (a classic SFTP drop artefact).

**Fix:** edit the agent's format explicitly rather than relying on inference.

```json
{
  "name": "events_agent",
  "format": {
    "type": "CSV",
    "delimiter": "|",
    "headerRows": 2,
    "quote": "'",
    "encoding": "ISO-8859-1"
  },
  "schema": { "fields": [] }
}
```

### 4. The flow succeeded but the destination table is empty

```text
# Symptom: the flow reports SUCCEEDED, the log shows no error, and the
# BigQuery table has zero rows.
```

**Cause:** two candidates, and you must distinguish them.

(a) **The output was written with `WRITE_TRUNCATE` and the load failed partway**, leaving the table empty. This is the dangerous one: the production table is now empty and the flow said "succeeded".

(b) **A recipe filtered everything out.** A filter on a nullable column silently drops every row when the predicate evaluates to `NULL` — the same SQL semantics as the Data Fusion chapter.

**Fix:** check the flow's log for the output row count first. If it says 0 rows, it is (b) and the filter is at fault. If it says N rows but the table is empty, it is (a) and the write disposition is at fault.

```bash
# The safe pattern: write to a staging table, then swap atomically.
bq query --use_legacy_sql=false '
CREATE OR REPLACE TABLE `my-project.analytics.events_summary`
AS SELECT * FROM `my-project.analytics.events_summary_staging`'
```

### 5. `OutOfMemoryError` / the agent crashes on a large dataset

```text
ERROR: com.google.dataprep.dataprep.DataprepServiceException:
Agent exited unexpectedly. Exit code 137 (SIGKILL). The agent ran out
of memory while profiling dataset events_500gb.
```

**Cause:** the agent heap was exhausted. Dataprep sizes the agent heuristically from the dataset, and for a large file with many wide string columns the heuristic under-provisions. Exit code 137 is the OOM-kill signature.

**Fix:** increase the agent size for the session, and profile a sample instead of the full dataset while exploring.

```bash
gcloud dataprep workspaces update my-workspace \
  --project=my-project --location=us-central1 \
  --update-agent-resources=default_agent_config=vm_config=vm_size='n1-standard-8'
```

### 6. `403 Quota exceeded` — BigQuery concurrent query limit on the workspace

```text
ERROR: com.google.cloud.bigquery.BigQueryException:
Exceeded rate limits: too many api requests per user per method for
method 'jobservice.jobquery'.
```

**Cause:** the Dataprep workspace is issuing many concurrent BigQuery jobs — one per user agent, plus one per recipe step, plus the profiling queries. A workspace with many active users plus a wide flow can exceed the per-user concurrent job limit.

**Fix:** reduce concurrency with an agent count limit, and reduce the number of recipe steps that each issue their own query.

```bash
gcloud dataprep workspaces update my-workspace \
  --project=my-project --location=us-central1 \
  --update-agent-count-limit=5
```

### 7. The output file in Cloud Storage has the wrong shape

```text
# Symptom: the CSV in GCS has a header row, embedded newlines inside
# quoted fields, and rows with a different field count than expected.
```

**Cause:** the output format was left as CSV with default settings, and the source contains values with embedded delimiters or newlines. The file looks fine when opened in a spreadsheet and is broken when parsed programmatically.

**Fix:** prefer Parquet or Avro for anything that will be reprocessed; if CSV is required, quote correctly and pin the delimiter in the output configuration.

```text
Output format: Parquet
Compression: SNAPPY
```

---

## 💡 Production Notes

- **Set the auto-stop timeout on every Dataprep workspace, on day one.** This is the single highest-value operational setting in the product. A forgotten session bills 24/7 until it is reclaimed. Default it to something aggressive — 30 minutes — and raise it only for known long jobs.

- **Understand that cost tracks attention, not data.** A user-hour is $0.60 whether you cleaned 1 MB or 500 GB. Model the bill as headcount × hours, then watch it with the Dataprep usage metrics. If the bill surprises you, it is almost always idle sessions rather than large datasets.

- **Cap the agent count per workspace.** `agent-count-limit` is the control that prevents one afternoon of enthusiastic exploration from becoming a fleet of billing agents.

- **Always profile a sample first, and the full dataset before asserting.** A 0.25% defect rate is invisible in a 10,000-row sample but is millions of rows at 500 GB. Assertions validated against a sample are not validated.

- **Commit the agent JSON to Git.** The agent is a versioned schema contract and a diffable description of the source. It also means that a schema change is a code review rather than a silent drift in someone's browser session.

- **Prefer Parquet and Avro over CSV above a few hundred MB.** Typed, columnar, no delimiter inference, no encoding ambiguity, no inference step. CSV only when the producer gives you nothing else.

- **Never let a production flow write directly with `WRITE_TRUNCATE` into a table anyone reads.** Write to a staging table and swap with `CREATE OR REPLACE TABLE AS SELECT`, which is atomic. A failed mid-run truncate leaves an empty production table behind a "successful" flow.

- **Schedule as the Dataprep service account and grant it its own permissions.** The manual run proves nothing about the schedule — different identity, different IAM. Test the schedule by triggering it, not by clicking Run.

- **Dataprep is the exploration phase, not the production phase.** Use it to profile, to discover the schema, and to export the agent file. Then move the transformation into BigQuery SQL or a Python job, where it is testable, reviewable, and cheap to run at scale.

- **Do not impute silently.** The "Missing values" recipe will happily fill a missing `amount` with the mean. Imputation is a business decision; make it explicit, log it, and prefer rejecting the row with a reason code — as `validate_event` does — when the value is an identifier or a key.

---

## 🔑 Key Takeaways

- **Dataprep is a browser-based data preparation service.** Its core value is *profiling* — showing you what is in the data — plus recipe-based reproducibility.
- **Billing is per user-hour, at $0.60.** The cost tracks *attention*, not data volume. Ten people idling in the tool cost more than one person cleaning a terabyte.
- **The per-user-agent runtime is the source of the trap.** Each user gets their own agent, and a forgotten session bills until it is reclaimed. Auto-stop is mandatory hygiene.
- **The flow is a DAG of datasets, not a chain of nodes.** N recipes means N+1 datasets, which makes Dataprep flows verbose compared to code.
- **Recipes cover set-based operations well** — joins, aggregates, dedup, pivot, cleanse — but cannot express custom functions, window functions with bespoke frames, or per-row error handling.
- **Assertions are dataset-level and boolean.** They are excellent for shape checks (row counts, nullability, uniqueness, schema) but they cannot produce the ten distinct reason codes that `validate_event` produces.
- **Type inference is the standout feature.** Dataprep distinguishes a phone number from a numeric ID from a quantity, and does not coerce a leading-zero postcode to an integer.
- **The agent JSON is the most underrated artefact.** It is a portable, diffable, versionable schema contract — download it and commit it to Git.
- **Prefer Parquet or Avro over CSV** above a few hundred MB: typed, columnar, no inference, no delimiter guessing.
- **The output write disposition matters.** `WRITE_TRUNCATE` into a production table, with a failure that still reports success, leaves an empty table. Stage, then swap atomically.
- **The three-way verdict:** Dataprep for exploration, SQL for production set-based transformations, Python for custom logic and per-row error handling. Use all three in that order.
- **Dataprep versus a SQL job is not close for a group-by.** `SELECT ... GROUP BY` over billions of rows in seconds, for cents, with Dataform tests, beats any canvas.

---

## 📚 Practice Exercises

1. **Cost model with idle sessions.** Use `estimate("dataprep", user_hours=...)` from `project/core/cost_model.py` to model three scenarios: (a) 8 analysts cleaning data 3 hours a week each; (b) 8 analysts 3 hours a week plus one agent left running overnight every night; (c) a single analyst doing a 200 GB profiling job once. Compute each monthly cost, identify the idle-session component in (b), and state the auto-stop setting you would apply.

2. **Assertion catalogue.** Write a Dataprep-style assertion set for the course pipeline: the row-count check, the `event_id` uniqueness and nullability checks, the `region` and `currency` domain checks, and the `amount >= 0` check. Then use `ingest_events` from `project/core/pipeline_logic.py` to evaluate each assertion against both `sample_data/events.csv` and `sample_data/malformed_events.csv`, and state which assertions detect the malformed file and which do not — and why.

3. **Reason-code gap analysis.** For each of the ten reason codes in `EXPECTED_REJECT_COUNTS`, determine whether a Dataprep assertion could detect it, and at what granularity (row-level or dataset-level). Produce two lists: "detectable with a Dataprep assertion" and "not representable in Dataprep". Then argue whether the undetectable set is acceptable for your use case.

4. **Agent file design.** Write the complete agent JSON for `sample_data/events.csv`, with a type and format regex for every column, and then write the modified agent for a version of the file that has a two-row header and a `|` delimiter. Then write the Python that would read both files with the standard library, and confirm that the agent's declared format matches what the code actually does.

5. **Three-way implementation.** Implement the per-region summary three ways: (a) a BigQuery SQL statement; (b) a sequence of Dataprep recipe steps with the agent and the output node configuration; (c) the Python using `aggregate_events` and `render_summary_csv`. Then argue, with the artefact count, the testability, and the cost, which one you would ship to production — and which one you would use to discover the schema in the first place.

6. **Sampling validity.** You have a 500 GB Parquet file with a known 0.4% duplicate rate. Dataprep's default exploration sample is 10,000 rows. Compute the probability that a 10,000-row sample contains zero duplicates, and explain what that means for a "no duplicate rows" assertion. Then specify a sampling strategy that would give a reliable duplicate-rate estimate.

7. **Write-disposition audit.** List every way a Dataprep flow can end with the wrong data in the destination table. For each, give the detection method (flow log, a BigQuery assertion query, a row-count comparison against the source) and the remediation. Include the case where the flow reports SUCCEEDED but the table is empty.

8. **Migration path.** Take a real messy dataset you know. Write the three-stage plan: what you do in Dataprep and what you export from it, what you implement in BigQuery SQL, and what you implement in Python. Then state the specific artefact that crosses each boundary, and why that artefact is the right one to carry.

---

## 📖 Further Reading

- [Cloud Dataprep Documentation](https://docs.cloud.google.com/dataprep/docs)
- [Dataprep — Data Preparation Overview](https://docs.cloud.google.com/dataprep/docs/introduction)
- [Dataprep — Managing Agents (Data Preparation)](https://docs.cloud.google.com/dataprep/docs/agents-overview)
- [Dataprep — Creating and Managing Flows](https://docs.cloud.google.com/dataprep/docs/flows)
- [Dataprep — Assertions](https://docs.cloud.google.com/dataprep/docs/assertions-overview)
- [Dataprep — Pricing](https://cloud.google.com/dataprep/pricing)
- [Dataprep — Using Dataprep with Dataplex](https://docs.cloud.google.com/dataprep/docs/dataplex-overview)
