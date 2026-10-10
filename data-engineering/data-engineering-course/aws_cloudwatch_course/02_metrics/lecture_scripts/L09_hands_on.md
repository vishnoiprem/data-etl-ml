---
lecture: L09
title: "Hands-on: build `put_metric_data.py` + 5 moto tests"
duration: "10:00"
section: 2
prereqs: ["L08"]
---

# L09 — Hands-on: build `put_metric_data.py` + 5 moto tests

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 2 — CloudWatch Metrics
> **Duration:** 10:00

## Prereqs

L08 (`put_metric_data` / `get_metric_data`).

## Key terms

- **Idempotency** — running the script twice should produce the same end
  state without raising.
- **`--dry-run`** — print the AWS API calls without making them. Combined
  with `moto`, this lets the tests run without real AWS credentials.
- **`moto.mock_aws`** — context manager / decorator that mocks every
  `boto3.client` call for the duration of the test.

## Lecture

This lecture walks you through the `02_metrics/code/put_metric_data.py`
script and its 5 moto tests. The script is **idempotent** (safe to
re-run) and accepts `--dry-run`.

### What the script does

1. Creates a custom namespace `MyApp` (CloudWatch namespaces are
   implicit — they "exist" the first time a metric is published).
2. Publishes 5 datapoints to a `LatencyMs` metric with two dimensions:
   `Endpoint` and `Region`.
3. Reads back `Average` and `p99` statistics over the last 5 minutes.
4. Lists the metrics and confirms the namespace / dimensions are
   present.

### How to run

```bash
cd aws_cloudwatch_course
source .venv/bin/activate         # if you ran bootstrap.sh
python3 02_metrics/code/put_metric_data.py
# or, dry-run:
python3 02_metrics/code/put_metric_data.py --dry-run
```

### How the tests work

`test_put_metric_data.py` uses `moto.mock_aws` to mock every `boto3`
call. Five tests cover the surface area:

1. `test_put_metric_data_publishes_datapoints` — verifies the API call
   was made with the right `MetricData` shape.
2. `test_get_metric_statistics_returns_avg_and_p99` — verifies a query
   for `Average` and `p99` returns the right value range.
3. `test_dimensions_filter_isolates_endpoints` — verifies that querying
   with a specific `Endpoint` dimension only returns that endpoint's
   series.
4. `test_dry_run_does_not_call_put_metric_data` — verifies the
   `--dry-run` flag suppresses the `put_metric_data` call.
5. `test_namespace_exists_in_list_metrics` — verifies the namespace
   appears in `list_metrics`.

### Run the tests

```bash
cd aws_cloudwatch_course
python3 -m pytest 02_metrics/code/ -v
```

You should see **5 passed** in well under a second.

### Extending the script

A few small exercises to lock in the material:

- Add a `StatisticValues` (`min`, `max`, `sum`, `sample_count`) instead
  of a single `Value` (see L06).
- Add a second metric `Errors` and a metric-math `err_rate` query
  (see L07 / L08).
- Switch `StorageResolution` to `1` and watch the test for high-res
  queries still pass (L06).

## Hands-on

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-engineering-course/aws_cloudwatch_course

# 1. Run the script
python3 02_metrics/code/put_metric_data.py

# 2. Run the tests
python3 -m pytest 02_metrics/code/ -v
```

## Quiz prep

- Why is the script idempotent? (Idempotency is achieved by *upserting*
  metrics — CloudWatch doesn't have separate create / update calls.
  Re-running produces the same metric state.)
- What does `--dry-run` do? (Prints the call payloads, suppresses the
  `boto3` invocation.)
- How many moto tests cover the script? (5)

## Further reading

- `02_metrics/code/put_metric_data.py` — the script.
- `02_metrics/code/test_put_metric_data.py` — the tests.
- `02_metrics/code/README.md` — the section-level how-to.

## What's next

Section 3 — CloudWatch Logs.
