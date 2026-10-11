# Section 6 — Logs Insights + Subscriptions + Kinesis / Firehose

> 5 lectures, ~60 minutes. Real-time log fan-out, filter-pattern syntax,
> Kinesis / Firehose / Lambda destinations, and a complete `boto3 + moto`
> working demo.

| L# | Title | File |
|---|---|---|
| L25 | Subscription Filters 101 — Real-Time Log Fan-out | `lecture_scripts/L25_subscription_filters.md` |
| L26 | Filter Pattern Syntax — exact, json, space-delimited tokens | `lecture_scripts/L26_filter_patterns.md` |
| L27 | Kinesis Data Streams + Firehose as Destinations | `lecture_scripts/L27_kinesis_firehose.md` |
| L28 | Lambda as Subscription Destination | `lecture_scripts/L28_lambda_destination.md` |
| L29 | Hands-on: `subscription_filter.py` + 4 moto tests | `lecture_scripts/L29_hands_on.md` |

**Working demo:** `code/subscription_filter.py` (idempotent,
`--dry-run`) + `code/test_subscription_filter.py` (4 moto tests).
