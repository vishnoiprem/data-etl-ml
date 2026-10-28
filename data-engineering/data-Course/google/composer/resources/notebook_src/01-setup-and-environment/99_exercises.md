## Exercises

1. **Environment audit.** Write a function `audit_environment()` that returns a dict of booleans covering: Python version, jinja2 present, pandas present, sample data present, and the local runner importable. Print it.
2. **Harder — reject anatomy.** Load `malformed_orders.csv`, call `transform_orders`, and print each rejected row's `reason`, `detail` and the first 60 characters of `raw`. Then explain, in a markdown cell, why the reason codes are low-cardinality but the raw payload is not.
3. **Harder — the 3755-row gap.** Explain in prose exactly where the 5000 − 1245 = 3755 non-accepted rows went. Verify your explanation numerically using the status and validity counters you computed earlier. Include what would happen to an `active` order if the pipeline only ever selected `complete` rows.
