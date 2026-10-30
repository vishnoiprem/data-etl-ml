# The Project — A Local BI Engine

> Everything here runs **locally with no GCP account, no credentials, and no bill**.
> Pure standard library. `pytest` finishes in about two seconds.

---

## What this is

A working **semantic layer** with a **query engine** and a **validation gate** —
the three things every BI tool gives you and most BI courses only describe.

| File | What it is |
|------|------------|
| `core/model.py` | The semantic layer: measures, dimensions, joins, models, explores, and the aggregation engine |
| `core/date_helpers.py` | Date spines, timeframe truncation, date filters, period-over-period |
| `core/lookml.py` | A LookML reader and writer — parse a view, render one, check its references |
| `core/validate.py` | The validation gate: grain, referential integrity, completeness, freshness |
| `local_bi.py` | The CLI that ties it together |
| `lookml/ecommerce.model.lookml` | The semantic layer rendered as LookML — the file a Looker developer commits |
| `tests/` | 145 tests, all offline |

The design decision that makes it work: **`core/` is pure standard library.** The
semantic layer is the hard part, and it must be testable without a network, a
credential or a Looker instance. `local_bi.py` is the only file that touches the
outside world — and it only touches files.

---

## The 5-minute path

```bash
cd data-engineering/data-Course/google/data-analysis

python3 -m venv .venv
source .venv/bin/activate

pip install -r project/requirements.txt

# Generate the deterministic dataset
python resources/sample_data.py --output-dir ./sample_data

# See the semantic layer
python project/local_bi.py describe

# Ask a question
python project/local_bi.py query \
    --input ./sample_data/orders.csv \
    --dimensions region \
    --measures total_revenue,distinct_orders

# Run the tests
python3 -m pytest project/tests/ -q
```

---

## The commands

### `describe` — what the semantic layer says

```bash
python project/local_bi.py describe
```

```
Model: orders
  label        : Orders
  table        : analytics.orders
  grain        : one row per order line
  primary key  : line_id
  description  : One row per order line. Note the grain: a single order with three lines appears three times.

  Measures:
    total_revenue          sum            additive      Sum of order line revenue.
    order_count            count          non-additive  Number of order lines. To count orders rather than lines, use count_distinct on order_id.
    distinct_orders        count_distinct non-additive  Number of unique orders.
    average_order_value    avg            additive      Average revenue per order line.
    gross_margin           sum            non-additive  Margin over revenue.
```

Read the two columns that matter: the **grain**, and whether each measure is
**additive**. Everything else in BI flows from those two facts.

### `query` — aggregate the fact table

```bash
python project/local_bi.py query \
    --input ./sample_data/orders.csv \
    --dimensions region,channel \
    --measures total_revenue,gross_margin
```

```
region  channel  total_revenue  gross_margin
-------  -------  -------------  -------------
AMER     app      38210.55       0.4211
...
```

`--format csv` and `--format json` also work; `--output FILE` writes to disk.

### `explores` — see the fan-out risk

```bash
python project/local_bi.py explores
```

```
  customers
    base model : customers
    join orders           one_to_many    FAN-OUT — measures on the far side will inflate
    warning: traversing a fan-out join multiplies the rows.
```

### `validate` — the gate

```bash
python project/local_bi.py validate --input ./sample_data/orders.csv
```

```
Validation report
----------------------------------------------------
  source            : ./sample_data/orders.csv
  rows checked      : 901
  result            : FAIL
  findings:
    [ERROR  ] grain.not_unique: primary key 'line_id' is not unique: 1 value(s) repeat. Every measure over this table is inflated. (1 rows)
    [ERROR  ] freshness.stale: newest row in 'created_at' is 126 day(s) old; the limit is 2. The numbers are not current — say so on the dashboard. (1 rows)
    [WARNING] value.negative: 1 row(s) have a negative 'total_amount'. Legitimate for refunds; suspicious for a sign-flip bug. (1 rows)
```

The exit code is **1** when the validation fails. Put it in CI and a broken
dashboard never ships.

### `spine` — fill the gaps

```bash
python project/local_bi.py spine \
    --input ./sample_data/orders.csv \
    --timeframe day \
    --output ./out/spine.csv
```

```
Date spine
----------------------------------------------------
  source            : ./sample_data/orders.csv
  timeframe         : day
  buckets           : 177
  buckets with data : 168
  empty buckets     : 9

  The empty buckets — these are the gaps a raw chart shows:
    2026-01-03
    2026-01-31
    2026-02-22
    ...
```

### `lookml` — render the semantic layer

```bash
python project/local_bi.py lookml --with-explores \
    --output project/lookml/ecommerce.model.lookml
```

---

## Break it on purpose

The fastest way to learn the grain is to make the number wrong and see it move.

### 1. Make the grain wrong

Add a second line to an order and watch the revenue change:

```bash
python3 - <<'PY'
import csv, sys
sys.path.insert(0, "project/core")
from model import build_sales_model, aggregate

rows = list(csv.DictReader(open("sample_data/orders.csv")))
model = build_sales_model()

before = aggregate(model, rows, ["region"], ["total_revenue"])
print("before:", sum(r.measures["total_revenue"] for r in before.rows))

# Duplicate every row — the classic fan-out.
doubled = rows + rows
after = aggregate(model, doubled, ["region"], ["total_revenue"])
print("after: ", sum(r.measures["total_revenue"] for r in after.rows))
PY
```

Every number doubles. The chart still looks like a chart.

### 2. Break the ratio

```bash
python3 - <<'PY'
import csv, sys
sys.path.insert(0, "project/core")
from model import build_sales_model, aggregate

rows = list(csv.DictReader(open("sample_data/orders.csv")))
model = build_sales_model()

result = aggregate(model, rows, ["region"], ["gross_margin"])
print("correct:", [r.measures["gross_margin"] for r in result.rows])

# The wrong way: average the per-row ratios.
from collections import defaultdict
per_row = defaultdict(list)
for row in rows:
    amount = float(row["total_amount"] or 0)
    margin = float(row["margin_amount"] or 0)
    if amount:
        per_row[row["region"]].append(margin / amount)
print("wrong:  ", [round(sum(v) / len(v), 4) for v in per_row.values()])
PY
```

The two differ, and the difference grows with the spread of the data.

### 3. Delete a dimension value

```bash
python3 - <<'PY'
import csv, sys
sys.path.insert(0, "project/core")
from model import build_sales_model, aggregate

rows = list(csv.DictReader(open("sample_data/orders.csv")))
model = build_sales_model()

before = aggregate(model, rows, ["region"], ["total_revenue"])
print("before:", sum(r.measures["total_revenue"] for r in before.rows))

for row in rows:
    row["region"] = None

after = aggregate(model, rows, ["region"], ["total_revenue"])
print("after: ", sum(r.measures["total_revenue"] for r in after.rows))
print("groups:", [(r.dimensions["region"]) for r in after.rows])
PY
```

The rows do not disappear — they collect under a `None` bucket. A total that
still looks right, with a breakdown that is silently wrong.

---

## The LookML file

`lookml/ecommerce.model.lookml` is generated from `core/model.py`:

```bash
python project/local_bi.py lookml --with-explores \
    --output project/lookml/ecommerce.model.lookml
```

A test asserts the committed file matches the generator, so the two can never
drift apart silently. The LookML file is what a Looker developer would commit;
the Python model is the source of truth.

```lookml
view: orders {
  label: "Orders"
  description: "One row per order line. Note the grain: a single order with three lines appears three times."
  # Grain: one row per order line
  sql: "select * from analytics.orders";

  dimension: created_at {
    label: "Order Date"
    type: time
    sql: "created_at"
    timeframe: "raw, day, week, month, quarter, year"
    description: "When the order was placed."
  }

  measure: gross_margin {
    label: "Gross Margin"
    type: ratio
    sql: "margin_amount"
    filters: "total_amount"
    description: "Margin over revenue."
  }

  join: customers {
    relationship: many_to_one
    sql_on: "orders.customer_id = customers.customer_id"
  }
}
```

Note `type: ratio` on `gross_margin`. That single line is what stops the BI tool
averaging the per-row ratios — the exact mistake the aggregation engine in
`core/model.py` refuses to make.

---

## The tests

```bash
python3 -m pytest project/tests/ -q
```

```
145 passed in 2.21s
```

| File | Tests | Covers |
|------|-------|--------|
| `tests/test_model.py` | 41 | Measures, dimensions, joins, grains, the aggregation engine |
| `tests/test_date_helpers.py` | 44 | Date spines, timeframe truncation, date filters, previous periods |
| `tests/test_lookml.py` | 23 | The LookML reader, the writer, the round trip, reference checking |
| `tests/test_validate.py` | 19 | Grain, referential integrity, completeness, freshness, negative values |
| `tests/test_cli.py` | 18 | Every subcommand, end to end, against the real data |

The tests that matter most:

- `test_a_ratio_is_not_the_average_of_per_row_ratios` — the ratio semantics.
- `test_a_repeated_order_id_is_not_a_grain_error` — the grain is the line, not
  the order.
- `test_the_shipped_lookml_matches_the_generator` — the committed LookML is
  current.

---

## The one-line mental model

> A measure is an aggregation with a type. A dimension is a grouping key. A
> join has a cardinality. A model has a grain. Get the grain and the
> cardinality right and the numbers are right; get either wrong and no
> dashboard will tell you.
