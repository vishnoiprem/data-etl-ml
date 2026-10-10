# Section 5 — CloudWatch Dashboards

> 5 lectures, ~55 minutes. Dashboards 101, every widget type, cross-region
> / cross-account, boto3 + moto working demo.

| L# | Title | File |
|---|---|---|
| L20 | Dashboards 101 — Body JSON, Widget Coordinate System | `lecture_scripts/L20_dashboards_101.md` |
| L21 | Widget Types — Metric, Logs Table, Logs Insights, Text, Stacked | `lecture_scripts/L21_widget_types.md` |
| L22 | Cross-Region / Cross-Account Dashboards | `lecture_scripts/L22_cross_region_account.md` |
| L23 | `put_dashboard` + `get_dashboard` with boto3 | `lecture_scripts/L23_boto3_dashboards.md` |
| L24 | Hands-on: `create_dashboard.py` + 4 moto tests | `lecture_scripts/L24_hands_on.md` |

**Working demo:** `code/create_dashboard.py` (idempotent, `--dry-run`)
+ `code/test_create_dashboard.py` (4 moto tests).
