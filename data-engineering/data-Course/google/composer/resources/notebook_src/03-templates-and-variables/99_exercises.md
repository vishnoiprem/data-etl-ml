## Exercises

1. **A template that must not fail.** Write a template that renders the target bucket, the logical date and the DAG id, and that falls back to a default bucket when the Variable is missing. Render it against a context with and without the Variable.
2. **Harder — detect the unrendered template.** Airflow only renders attributes listed in `template_fields`. Write a small function `is_rendered(value)` that returns `False` when a string still contains `{{` or `}}`. Apply it to the rendered output of the `templating_paths` DAG for every path, and explain what it would mean if one of them came back `False`.
3. **Harder — params vs Variables.** Build two contexts for the same logical date: one where `target_bucket` is a Variable and one where it is a param. Use the layering template `{{ params.target_bucket | default(var.value.target_bucket) }}`. Show that the param wins, and explain which one a *backfill trigger* should use and why.
