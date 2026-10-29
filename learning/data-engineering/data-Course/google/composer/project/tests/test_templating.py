"""
test_templating.py — tests for the Airflow-style Jinja templating model.

These tests demonstrate the templating semantics that matter in a real
DAG, without needing Airflow installed.
"""
from __future__ import annotations

import pytest

from templating import (
    TemplateRenderError,
    build_context,
    render_all,
    render_template,
)


class TestBuildContext:
    """Tests for :func:`build_context`."""

    def test_ds_is_the_logical_date(self, context):
        assert context["ds"] == "2026-01-15"

    def test_ds_nodash(self, context):
        assert context["ds_nodash"] == "20260115"

    def test_prev_ds(self, context):
        assert context["prev_ds"] == "2026-01-14"

    def test_next_ds(self, context):
        assert context["next_ds"] == "2026-01-16"

    def test_data_interval_is_half_open(self, context):
        assert context["data_interval_start"].startswith("2026-01-15")
        assert context["data_interval_end"].startswith("2026-01-16")

    def test_dag_and_task_in_object_graph(self, context):
        assert context["dag"]["dag_id"] == "test_dag"
        assert context["task"]["task_id"] == "test_task"

    def test_params_exposed(self, context):
        assert context["params"]["audience"] == "testers"


class TestRenderTemplate:
    """Tests for :func:`render_template`."""

    def test_renders_ds(self, context):
        assert render_template("{{ ds }}", context) == "2026-01-15"

    def test_renders_ds_nodash(self, context):
        assert render_template("{{ ds_nodash }}", context) == "20260115"

    def test_renders_variable(self, context):
        assert render_template("{{ var.value.gcp_project_id }}", context) == "demo-project"

    def test_renders_variable_without_value_attribute(self, context):
        assert render_template("{{ var.gcp_project_id }}", context) == "demo-project"

    def test_renders_connection_field(self, context):
        assert render_template("{{ conn.http_orders_api.host }}", context) == "api.example.com"

    def test_renders_connection_extra_as_json(self, context):
        rendered = render_template("{{ conn.http_orders_api.extra_dejson.timeout }}", context)
        assert rendered == "30"

    def test_renders_param(self, context):
        assert render_template("{{ params.audience }}", context) == "testers"

    def test_renders_dag_id(self, context):
        assert render_template("{{ dag.dag_id }}", context) == "test_dag"

    def test_renders_prev_ds(self, context):
        assert render_template("{{ prev_ds }}", context) == "2026-01-14"

    def test_compound_path(self, context):
        template = "gs://{{ var.value.source_bucket }}/{{ ds }}/orders.csv"
        assert render_template(template, context) == "gs://demo-bucket/2026-01-15/orders.csv"

    def test_undefined_variable_raises(self, context):
        """A missing variable is a hard error, not an empty string.

        This is why an Airflow DAG with a typo in a Variable name fails
        loudly instead of silently writing to a path with a blank
        component.
        """
        with pytest.raises(TemplateRenderError):
            render_template("{{ var.value.does_not_exist }}", context)

    def test_undefined_in_strict_mode_raises(self, context):
        with pytest.raises(TemplateRenderError):
            render_template("{{ nothing_at_all }}", context)

    def test_default_filter_handles_missing_variable(self, context):
        template = "{{ var.value.missing | default('fallback') }}"
        assert render_template(template, context) == "fallback"

    def test_default_filter_used_when_variable_present(self, context):
        template = "{{ var.value.gcp_project_id | default('fallback') }}"
        assert render_template(template, context) == "demo-project"

    def test_error_carries_the_template(self, context):
        with pytest.raises(TemplateRenderError) as excinfo:
            render_template("{{ broken }}", context)
        assert "{{ broken }}" in str(excinfo.value)


class TestRenderAll:
    """Tests for :func:`render_all`."""

    def test_renders_every_template(self, context):
        rendered = render_all(
            {"a": "{{ ds }}", "b": "{{ ds_nodash }}"},
            context,
        )
        assert rendered == {"a": "2026-01-15", "b": "20260115"}


class TestMacroLikeBehaviour:
    """Tests for the arithmetic Airflow macros provide."""

    def test_date_arithmetic_via_python(self):
        """Airflow's `macros.ds_add` is Jinja arithmetic on dates.

        The same result is achievable in a template with a small helper,
        which is why `macros` exists at all.
        """
        from datetime import datetime, timedelta

        ctx = build_context(logical_date="2026-01-15")
        ctx["macros"] = {
            "ds_add": lambda ds, days: (
                datetime.strptime(ds, "%Y-%m-%d") + timedelta(days=days)
            ).date().isoformat()
        }
        rendered = render_template("{{ macros.ds_add(ds, -1) }}", ctx)
        assert rendered == "2026-01-14"
