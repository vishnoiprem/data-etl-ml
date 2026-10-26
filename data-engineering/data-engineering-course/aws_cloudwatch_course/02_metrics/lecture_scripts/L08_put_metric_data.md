---
lecture: L08
title: "`put_metric_data` + `get_metric_data` with boto3"
duration: "18:00"
section: 2
prereqs: ["L07"]
---

# L08 — `put_metric_data` + `get_metric_data` with boto3

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 2 — CloudWatch Metrics
> **Duration:** 18:00

## Prereqs

L07 (statistics). Working knowledge of `boto3.client("cloudwatch")`.

## Key terms

- **`put_metric_data`** — boto3 client method to publish one or more
  metric datapoints. Idempotent, but each call counts as a *data point*
  for billing.
- **`get_metric_data`** — modern (post-2018) API to query metrics
  including **metric math** expressions. Preferred over
  `get_metric_statistics`.
- **`get_metric_statistics`** — older API that returns
  `{Statistic: value}` rows. Use only when you need the older shape.
- **Pagination token** — `get_metric_data` returns up to 100,800
  datapoints per call; if more, the response includes `NextToken`.
- **Boto3 client vs. resource** — CloudWatch has a client only. There
  is no `boto3.resource("cloudwatch")`.

## Lecture

The two API calls you'll use 95% of the time are `put_metric_data` and
`get_metric_data`. Let's see them end to end.

### `put_metric_data` — publishing

```python
import boto3
from datetime import datetime

cw = boto3.client("cloudwatch")

cw.put_metric_data(
    Namespace="MyApp",
    MetricData=[
        {
            "MetricName": "LatencyMs",
            "Value": 87.4,
            "Unit": "Milliseconds",
            "Timestamp": datetime.utcnow(),
            "Dimensions": [
                {"Name": "Endpoint",  "Value": "/checkout"},
                {"Name": "Region",    "Value": "us-east-1"},
            ],
            # Optional: "StorageResolution": 1,  # 1-sec high-res
        },
    ],
)
```

You can pass up to **1,000 datapoints** in a single call. The unit
field is free-form but use the standard set: `Seconds`, `Bytes`,
`Percent`, `Count`, `Milliseconds`, etc.

### `get_metric_data` — querying (modern API)

```python
from datetime import datetime, timedelta

end   = datetime.utcnow()
start = end - timedelta(hours=1)

resp = cw.get_metric_data(
    StartTime=start,
    EndTime=end,
    MetricDataQueries=[
        # 1) Raw metric
        {
            "Id": "lat",
            "MetricStat": {
                "Metric": {
                    "Namespace":  "MyApp",
                    "MetricName": "LatencyMs",
                    "Dimensions": [
                        {"Name": "Endpoint", "Value": "/checkout"},
                    ],
                },
                "Period": 60,
                "Stat":   "p99",
            },
            "ReturnData": True,
        },
        # 2) Error rate via metric math
        {
            "Id": "err_rate",
            "Expression": "errors / invocations * 100",
            "Label":      "Error rate (%)",
            "ReturnData": True,
        },
        # 3) Underlying metrics used by the math expression
        {"Id": "errors",
         "MetricStat": {"Metric": {"Namespace": "MyApp",
                                   "MetricName": "Errors"},
                        "Period": 60, "Stat": "Sum"},
         "ReturnData": False},
        {"Id": "invocations",
         "MetricStat": {"Metric": {"Namespace": "MyApp",
                                   "MetricName": "Invocations"},
                        "Period": 60, "Stat": "Sum"},
         "ReturnData": False},
    ],
)
for series in resp["MetricDataResults"]:
    print(series["Id"], series["Label"], series["Values"])
```

`get_metric_data` returns **timestamped values** rather than aggregated
rows; it's the right choice for any code that has to do further math
or feed a plot.

### `get_metric_statistics` — the older API

Still works and is sometimes easier for one-off queries:

```python
resp = cw.get_metric_statistics(
    Namespace="MyApp",
    MetricName="LatencyMs",
    Dimensions=[{"Name": "Endpoint", "Value": "/checkout"}],
    StartTime=start,
    EndTime=end,
    Period=300,
    Statistics=["Average", "p99"],
)
# resp["Datapoints"] -> [{"Timestamp": ..., "Average": ..., "p99": ...}, ...]
```

Prefer `get_metric_data` for new code; reach for
`get_metric_statistics` only when you need the older shape.

### `list_metrics` — discoverability

```python
resp = cw.list_metrics(
    Namespace="MyApp",
    MetricName="LatencyMs",
    Dimensions=[{"Name": "Endpoint", "Value": "/checkout"}],
)
for m in resp["Metrics"]:
    print(m["Namespace"], m["MetricName"], m["Dimensions"])
```

Use this to enumerate time-series when you don't know the dimension
values in advance (e.g. building a "show me all my endpoints"
dashboard).

### Common pitfalls

1. **Timestamp drift** — datapoints older than 2 weeks or more than 2
   hours in the future are *rejected*. Always use a sane `Timestamp`.
2. **High-resolution metrics and standard-resolution queries** — you
   can query a high-res metric at 1-min resolution, but not the other
   way around. Don't try.
3. **Different time zones** — `boto3` serialises datetimes as
   ISO-8601; pass `datetime` objects, not `time.time()` floats.
4. **`return_data` is the default for non-math queries** — but for math
   *expressions*, the engine requires you to set `ReturnData` on every
   member, including the false-flagged sources.

## Hands-on

We'll wire all of this up into a working `boto3 + moto` script in L09.
For now, run the following against your AWS account:

```python
import boto3
from datetime import datetime, timedelta

cw = boto3.client("cloudwatch")
end = datetime.utcnow()
start = end - timedelta(hours=1)

# 1. Put a single datapoint
cw.put_metric_data(
    Namespace="MyApp",
    MetricData=[{
        "MetricName": "LatencyMs",
        "Value": 87.4,
        "Unit": "Milliseconds",
        "Dimensions": [{"Name": "Endpoint", "Value": "/demo"}],
    }],
)

# 2. Read it back
resp = cw.get_metric_data(
    StartTime=start,
    EndTime=end,
    MetricDataQueries=[{
        "Id": "lat",
        "MetricStat": {
            "Metric": {"Namespace": "MyApp", "MetricName": "LatencyMs",
                       "Dimensions": [{"Name": "Endpoint", "Value": "/demo"}]},
            "Period": 60,
            "Stat":   "p99",
        },
        "ReturnData": True,
    }],
)
print(resp["MetricDataResults"])
```

## Quiz prep

- What is the max datapoints per `put_metric_data` call?
  (1,000)
- Which API supports metric math expressions?
  (`get_metric_data`)
- What's the default statistic on a metric graph? (Average)

## Further reading

- `https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html`
- L09 — Hands-on (builds a working script).

## What's next

L09 — Hands-on: build `put_metric_data.py` + 5 moto tests.
