```python
# Exercise 1
TEMPLATE = (
    "gs://{{ var.value.target_bucket | default('fallback-bucket') }}"
    "/{{ dag.dag_id }}/{{ ds }}/summary.csv"
)

ctx_no_var = build_context(dag_id="etl_to_gcs", logical_date="2026-01-15")
print(render_template(TEMPLATE, ctx_no_var))
# gs://fallback-bucket/etl_to_gcs/2026-01-15/summary.csv

ctx_with_var = build_context(
    dag_id="etl_to_gcs",
    logical_date="2026-01-15",
    variables={"target_bucket": "real-bucket"},
)
print(render_template(TEMPLATE, ctx_with_var))
# gs://real-bucket/etl_to_gcs/2026-01-15/summary.csv
```

```python
# Exercise 2
def is_rendered(value):
    return isinstance(value, str) and "{{" not in value and "}}" not in value

for key, value in rendered.items():
    print(f"{key:<10} rendered={is_rendered(value)}  {value}")
```

If a value comes back `False`, the template string was never rendered at
all — it reached the task body as a literal string. The cause is almost
always that the attribute holding it is not listed in the operator's
`template_fields`, so Airflow skipped it. It is *not* a context problem: a
context problem would raise a `TemplateRenderError`, not silently pass the
raw `{{ ... }}` through.

```python
# Exercise 3
LAYER = "{{ params.target_bucket | default(var.value.target_bucket) }}"

ctx_var_only = build_context(
    logical_date="2026-01-15", variables={"target_bucket": "var-bucket"}
)
ctx_both = build_context(
    logical_date="2026-01-15",
    variables={"target_bucket": "var-bucket"},
    params={"target_bucket": "param-bucket"},
)

print(render_template(LAYER, ctx_var_only))   # var-bucket
print(render_template(LAYER, ctx_both))       # param-bucket
```

A backfill trigger should use a **param**, because the target for a backfill
is a property of *that run* ("write this to the staging bucket"), not of the
environment. A Variable is for "which bucket does this environment use",
which is stable across runs. Using a Variable for a backfill destination
means every backfill run and the live schedule write to the same place,
which is how you end up with a backfill that truncates the live table.
