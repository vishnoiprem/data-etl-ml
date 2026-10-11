# `put_metric_data` — CloudWatch Metrics demo

> Companion to L08 / L09 of the AWS CloudWatch Crash Course.
> Author: Prem Vishnoi <pvishnoi@avilx.com>

## What it does

1. Publishes 5 datapoints to a custom namespace `MyApp/Latency` under
   the `MyApp` namespace, with `Endpoint` and `Region` dimensions.
2. Reads back `Average` and `p99` statistics over the last 5 minutes via
   `get_metric_statistics`.
3. Confirms the namespace and dimensions exist via `list_metrics`.

## How to run

```bash
# From the course root
python3 02_metrics/code/put_metric_data.py
# Or, without making any AWS calls:
python3 02_metrics/code/put_metric_data.py --dry-run
```

Required IAM permissions for the real (non-dry-run) call:

```
cloudwatch:PutMetricData
cloudwatch:GetMetricStatistics
cloudwatch:ListMetrics
```

## How to test

```bash
python3 -m pytest 02_metrics/code/ -v
```

5 tests pass against `moto.mock_aws` (no AWS credentials required).
