# `create_dashboard` — CloudWatch Dashboards demo

> Companion to L23/L24. Author: Prem Vishnoi <prem.vishnoi@example.com>

## What it does

Builds a 3-widget dashboard `checkout-overview`:

1. **Metric** widget — `AWS/ApiGateway Latency p99` for `checkout`.
2. **Log** widget — top 20 ERRORs in `/aws/lambda/checkout`.
3. **Text** widget — markdown runbook.

## Run

```bash
python3 05_dashboards/code/create_dashboard.py
python3 05_dashboards/code/create_dashboard.py --dry-run
```

Required IAM permissions (real AWS):

```
cloudwatch:PutDashboard
cloudwatch:GetDashboard
cloudwatch:ListDashboards
```

## Test

```bash
python3 -m pytest 05_dashboards/code/ -v
```

4 moto tests pass; no AWS credentials needed.
