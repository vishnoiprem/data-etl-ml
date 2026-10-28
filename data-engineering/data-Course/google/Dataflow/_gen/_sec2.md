### The rule that actually bites: the name must be constant

**A metric's namespace and name must be compile-time constants.**

Beam identifies a metric by its `(namespace, name)` pair. If you build the
name from the *data* -- `f"revenue_{region}"` -- then every distinct value
produces a distinct metric. Three regions is fine. Thirty thousand customer
IDs is a metric-cardinality explosion that will overwhelm the monitoring
backend and get your job throttled or rejected.

| Metric name | Safe? | Why |
|---|---|---|
| `"rows_seen"` | Yes | One metric, one time series |
| `f"rejected_{reason}"` | **No** | Unbounded series count |
| `f"revenue_{customer_id}"` | **No** | Unbounded series count |

### And a surprise: Beam 2.77 counters have no labels

You might expect to fix the cardinality problem with a *label* --
`counter.inc(label={"region": "AMER"})`. That is the API in some Beam
versions, and it is the natural instinct. **In Beam 2.77 it does not
exist**, and the error is not subtle:

```
TypeError: __call__() got an unexpected keyword argument 'label'
```

The signature is `Metrics.counter(namespace, name)` -- two arguments, no
label parameter -- and the updater is `inc(value)`. The `MetricName`
dataclass *has* a `labels` field, but the public `Metrics.counter()`
constructor does not populate it.

So what do you actually do when you need per-region visibility? You have
three options, and the course project uses the first:

1. **A fixed, bounded set of metric names.** You know the dimensions in
   advance (`rows_seen_amer`, `rows_seen_apac`, ...). Simple, and works.
2. **Aggregate counters by category**, and keep the fine-grained breakdown
   in the *output data* rather than in the metrics.
3. **Use a different mechanism** -- a `Distribution` for percentiles, or
   write the breakdown to BigQuery and query it there.

We will demonstrate the cardinality explosion live in section 2.4, and
show the bounded-name fix next to it. The explosion fails *silently* on a
laptop and fails loudly in production, which is exactly the kind of bug
worth knowing about.
