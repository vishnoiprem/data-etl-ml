"""The code cells for notebook 08 section 2, as a standalone module.

Kept separate so the generator file stays readable and the patcher can
swap the whole block in and out without nested-quote trouble.
"""

CELLS_SRC = []


def _add(source: str) -> None:
    CELLS_SRC.append(source)


_add(r'''
from apache_beam.metrics import Metrics, MetricsFilter

# --- The correct pattern -------------------------------------------------
# A class-level counter: one object, one metric, one time series.

class GoodInstrumentedFn(beam.DoFn):
    """Counts every row it sees, plus the revenue it carries."""

    ROWS_SEEN = Metrics.counter("dataflow_course", "rows_seen")
    REVENUE_EUR = Metrics.gauge("dataflow_course", "revenue_eur")

    def process(self, row):
        GoodInstrumentedFn.ROWS_SEEN.inc()
        GoodInstrumentedFn.REVENUE_EUR.set(row["amount"])
        yield row


# --- The cardinality trap -------------------------------------------------
# The metric NAME is built from the element.  Every distinct element value
# becomes its own metric.

class CardinalityTrapFn(beam.DoFn):
    """One metric per distinct region -- an explosion waiting to happen."""

    def process(self, row):
        Metrics.counter("dataflow_course", f"seen_{row['region']}").inc()
        yield row


# --- The bounded fix ------------------------------------------------------
# The dimensions are known in advance, so the metric names are too.

KNOWN_REGIONS = ("AMER", "APAC", "EMEA", "LATAM")


class BoundedNamesFn(beam.DoFn):
    """One counter per KNOWN region -- a bounded, fixed set of metrics."""

    def process(self, row):
        region = row["region"]
        if region in KNOWN_REGIONS:
            Metrics.counter("dataflow_course", f"seen_{region.lower()}").inc()
        yield row


# --- The attempt to use a label -------------------------------------------
# This is the API you would expect.  It does not exist in Beam 2.77.
try:
    Metrics.counter("dataflow_course", "probe").inc(label={"region": "AMER"})
    print("label= accepted -- labels are available")
except TypeError as exc:
    print(f"label= REJECTED -> TypeError: {exc}")

print()
print("Metrics.counter     :", hasattr(Metrics, "counter"))
print("Metrics.gauge       :", hasattr(Metrics, "gauge"))
print("Metrics.distribution:", hasattr(Metrics, "distribution"))
print("MetricsFilter methods:", [m for m in dir(MetricsFilter) if m.startswith("with_")])
''')

_add(r'''
### 2.3 Reading metrics back

The read API has three moving parts:

- `pipeline_result.metrics()` -> the whole metric store for the run
- `.query(filter)` -> a dict keyed by **category**, not by namespace
- `MetricsFilter()` -> narrows by namespace, name, or step

The shape surprises people, so here it is exactly:

```python
{
  "counters":      [MetricResult, ...],
  "gauges":        [MetricResult, ...],
  "distributions": [MetricResult, ...],
  "histograms":    [...],
  "string_sets":   [...],
  "bounded_tries": [...],
}
```

The top-level keys are the metric **categories**. The namespace and name
live on each result, at `metric_result.key.metric.namespace` and
`metric_result.key.metric.name`. There is no top-level namespace map --
you have to walk the list yourself.

| Filter method | Narrows to |
|---|---|
| `with_namespace("ns")` | one namespace |
| `with_name("name")` | one metric name within the namespace |
| `with_step("step")` | one transform step |

One more surprise: the same metric name can appear under **several steps**,
each with its own committed value. A counter incremented in two different
`ParDo`s reports as two results, and you have to sum them.
''')

_add(r'''
rows = [
    {"region": "AMER", "amount": 10.0},
    {"region": "APAC", "amount": 20.0},
    {"region": "AMER", "amount": 5.0},
    {"region": "EMEA", "amount": 7.5},
]

with beam.Pipeline(options=options) as p:
    (p
     | "Rows" >> beam.Create(rows)
     | "Good" >> beam.ParDo(GoodInstrumentedFn())
     | "Trapped" >> beam.ParDo(CardinalityTrapFn())
     | "Bounded" >> beam.ParDo(BoundedNamesFn()))

pipeline_result = p.result
pipeline_result.wait_until_finish()

queried = pipeline_result.metrics().query(
    MetricsFilter().with_namespace("dataflow_course")
)

print("top-level keys (categories):", sorted(queried.keys()))
print()
print("counters in the 'dataflow_course' namespace:")
for metric_result in queried.get("counters", []):
    metric = metric_result.key.metric
    print(f"  {metric.name:<20} committed={metric_result.committed!s:<6} "
          f"step={metric_result.key.step}")
''')

_add(r'''
### 2.4 The failure, demonstrated

Look at the counters printed above:

- `Good` produced exactly **one** metric, `rows_seen`, with a committed
  value of 4 -- the four input rows.
- `Trapped` produced **one metric per distinct region**, because the metric
  name was built from the data. Four rows, three metrics.

Now imagine the same code keyed on `customer_id` instead of `region`. The
metric count becomes the number of distinct customers, and the Dataflow
monitoring backend has to store, index, and alert on every one of them.
The job does not crash. The job gets *slow*, then starts getting throttled,
and the pipeline falls behind with no obvious cause.

This is the failure mode a laptop will never warn you about, because on a
laptop the "monitoring backend" is a dictionary in memory.

### The fix, side by side

```python
# WRONG -- unbounded series count.
Metrics.counter("ns", f"seen_{row['region']}").inc()

# RIGHT, when the dimensions are known in advance -- bounded set of names.
if row["region"] in KNOWN_REGIONS:
    Metrics.counter("ns", f"seen_{row['region'].lower()}").inc()

# RIGHT, when they are not -- aggregate by category, and keep the
# fine-grained breakdown in the output data, not in the metrics.
Metrics.counter("ns", "rows_seen").inc()
```

The `Bounded` step above shows the middle option in action: four known
regions, four fixed metric names, and an unknown region would simply not
be counted -- which is a decision you make deliberately, not by accident.
''')

_add(r'''
# Count the series explosion directly -- the number that matters.
def series_for(namespace, category="counters"):
    names = []
    for metric_result in queried.get(category, []):
        metric = metric_result.key.metric
        if metric.namespace == namespace:
            names.append(metric.name)
    return sorted(names)


all_names = series_for("dataflow_course")
print(f"distinct counters in namespace 'dataflow_course': {len(all_names)}")
for name in all_names:
    print("   ", name)
print()

region_scoped = [n for n in all_names if n.startswith("seen_")]
print(f"metrics whose NAME encodes the region: {len(region_scoped)}")
for name in region_scoped:
    print("   ", name)
print()
print("Every one of those is a separate time series the monitoring backend")
print("has to store.  With four regions that is fine.  With four million")
print("customer IDs it is an outage.")
''')

_add(r'''
# Reading one specific metric back, and summing across steps.
filter_ = MetricsFilter().with_namespace("dataflow_course").with_name("rows_seen")
by_step = pipeline_result.metrics().query(filter_)

total = 0
print(f"{'step':<14} {'committed':>10}")
for metric_results in by_step.values():
    for metric_result in metric_results:
        committed = metric_result.committed
        if isinstance(committed, list):
            committed = committed[0] if committed else None
        total += committed or 0
        print(f"{metric_result.key.step:<14} {committed!s:>10}")
print(f"{'TOTAL':<14} {total:>10}   (4 input rows)")
''')
