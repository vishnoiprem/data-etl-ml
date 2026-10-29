"""
templating.py — Airflow-style Jinja templating, evaluated without Airflow.

Airflow renders every operator's ``template_fields`` with Jinja2 before the
task runs. The context is the heart of the feature:

    * ``{{ ds }}``             — the logical date, ``YYYY-MM-DD``
    * ``{{ ts }}``             — the logical date as a full timestamp
    * ``{{ data_interval_start }}`` / ``{{ data_interval_end }}``
    * ``{{ dag.dag_id }}``, ``{{ task.task_id }}``, ``{{ ti }}``
    * ``{{ var.value.my_var }}``     — an Airflow Variable
    * ``{{ conn.my_conn.host }}``    — an Airflow Connection
    * ``{{ params.my_param }}``      — a DAG-run parameter
    * ``{{ macros.ds_add(ds, -1) }}`` — a macro

This module reimplements that rendering with plain Jinja2 so the templating
behaviour can be demonstrated and tested on a machine with no Airflow
install. It is a **teaching model**, not a replacement: Airflow's own
rendering differs in the details (its context is richer, it adds
``{{ task_instance }}`` and macros, and it re-renders per task with
per-operator isolation).

The point of the exercise is to make the *mechanics* visible:

    1. The context is a plain dict.
    2. Templates are strings.
    3. Rendering happens **before** the task body runs.
    4. An undefined variable is a hard error, not an empty string — which
       is why Airflow fails the task at parse time rather than halfway
       through a production job.

Usage:
    from templating import render_template, build_context

    context = build_context(dag_id="etl_to_gcs", logical_date="2026-01-15")
    render_template("gs://bucket/{{ ds }}/orders.csv", context)
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Mapping

try:
    from jinja2 import BaseLoader, Environment, StrictUndefined, Undefined

    JINJA_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when Jinja2 is absent
    BaseLoader = object  # type: ignore[assignment,misc]
    Environment = None  # type: ignore[assignment,misc]
    StrictUndefined = None  # type: ignore[assignment,misc]
    Undefined = None  # type: ignore[assignment,misc]
    JINJA_AVAILABLE = False


class TemplateRenderError(RuntimeError):
    """Raised when a template cannot be rendered.

    Args:
        template: The offending template string.
        cause: The underlying exception, when there was one.
    """

    def __init__(self, template: str, cause: Exception | None = None) -> None:
        super().__init__(f"failed to render template: {template!r}")
        self.template = template
        self.cause = cause


def _iso(value: dt.datetime) -> str:
    """Render a datetime as an Airflow-style ISO timestamp."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(dt.timezone.utc).isoformat()


def build_context(
    *,
    dag_id: str = "example_dag",
    task_id: str = "example_task",
    logical_date: str = "2026-01-15",
    run_id: str | None = None,
    variables: Mapping[str, Any] | None = None,
    connections: Mapping[str, Any] | None = None,
    params: Mapping[str, Any] | None = None,
    data_interval_days: int = 1,
) -> dict[str, Any]:
    """Build the Jinja context Airflow would provide.

    The shape of this dict is the thing to internalise: Airflow builds one
    of these per task, per DAG run, and hands it to Jinja2.

    Args:
        dag_id: The DAG's identifier.
        task_id: The task's identifier.
        logical_date: The DAG run's logical date, ``YYYY-MM-DD``.
        run_id: The DAG run's identifier.
        variables: Airflow Variables, exposed as ``var``.
        connections: Airflow Connections, exposed as ``conn``.
        params: DAG-run params, exposed as ``params``.
        data_interval_days: Width of the data interval in days.

    Returns:
        The rendering context.
    """
    if "T" in logical_date:
        start = dt.datetime.fromisoformat(logical_date.replace("Z", "+00:00"))
        if start.tzinfo is None:
            start = start.replace(tzinfo=dt.timezone.utc)
    else:
        start = dt.datetime.strptime(logical_date, "%Y-%m-%d").replace(
            tzinfo=dt.timezone.utc
        )
    end = start + dt.timedelta(days=data_interval_days)

    resolved_run_id = run_id or f"manual__{start.date().isoformat()}T00:00:00+00:00"

    context: dict[str, Any] = {
        # Core date/time templates
        "ds": start.date().isoformat(),
        "ts": _iso(start),
        "ds_nodash": start.date().isoformat().replace("-", ""),
        "prev_ds": (start - dt.timedelta(days=1)).date().isoformat(),
        "next_ds": (start + dt.timedelta(days=1)).date().isoformat(),
        "data_interval_start": _iso(start),
        "data_interval_end": _iso(end),
        "logical_date": _iso(start),
        "run_id": resolved_run_id,
        # Object graph
        "dag": {"dag_id": dag_id},
        "task": {"task_id": task_id},
        "ti": {"task_id": task_id, "dag_id": dag_id, "run_id": resolved_run_id},
        # Collections — exposed via wrapper objects below
        "__variables__": dict(variables or {}),
        "__connections__": {
            name: _ConnectionView(spec) for name, spec in (connections or {}).items()
        },
        "params": dict(params or {}),
    }
    return context


class _ConnectionView:
    """A tiny stand-in for Airflow's ``conn`` object.

    Airflow exposes a connection's fields as attributes
    (``conn.my_conn.host``), with extras available under ``conn.my_conn.extra_dejson``.
    """

    def __init__(self, spec: Mapping[str, Any]) -> None:
        self._spec = dict(spec)

    def __getattr__(self, item: str) -> Any:
        if item.startswith("_"):
            raise AttributeError(item)
        if item == "extra_dejson":
            import json

            raw = self._spec.get("extra", "{}")
            try:
                return json.loads(raw)
            except (TypeError, ValueError):
                return {}
        if item in self._spec:
            return self._spec[item]
        raise AttributeError(
            f"connection has no attribute {item!r} "
            f"(available: {', '.join(sorted(self._spec)) or 'none'})"
        )

    def __repr__(self) -> str:
        return f"<ConnectionView {self._spec.get('conn_id', '?')}>"


class _VariableView:
    """A tiny stand-in for Airflow's ``var`` object."""

    def __init__(self, values: Mapping[str, Any]) -> None:
        self._values = dict(values)

    def __getattr__(self, item: str) -> Any:
        if item.startswith("_"):
            raise AttributeError(item)
        if item in self._values:
            return self._values[item]
        # Return an Undefined sentinel rather than raising immediately.
        # Jinja's `default` filter only works if the lookup *returns*
        # something undefined — an exception raised here would bypass
        # `default` entirely and fail the render. StrictUndefined still
        # raises when the value is actually used, so a missing variable
        # is still a hard error unless `| default(...)` is applied.
        if Undefined is not None:
            return StrictUndefined(
                name=f"variable {item!r} not found "
                f"(available: {', '.join(sorted(self._values)) or 'none'})"
            )
        raise KeyError(
            f"variable {item!r} not found "
            f"(available: {', '.join(sorted(self._values)) or 'none'})"
        )

    @property
    def value(self) -> "VariableView":
        """Return self, so ``var.value.name`` works.

        Airflow's ``var`` object exposes variables through a ``value``
        attribute (``var.value.my_var``) as well as directly
        (``var.my_var``). Both spellings appear in real DAGs, so both work.
        """
        return self

    def get(self, item: str, default: Any = None) -> Any:
        """Return a variable, or a default when it is absent.

        Args:
            item: The variable name.
            default: The value to return when the variable is missing.

        Returns:
            The variable's value, or ``default``.
        """
        return self._values.get(item, default)

    def json(self, item: str, default: Any = None) -> Any:
        """Return a variable parsed as JSON.

        Args:
            item: The variable name.
            default: The value to return when the variable is missing.

        Returns:
            The parsed JSON, or ``default``.
        """
        import json

        raw = self._values.get(item)
        if raw is None:
            return default
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return default

    def __repr__(self) -> str:
        return f"<VariableView {sorted(self._values)}>"


def render_template(template: str, context: Mapping[str, Any]) -> str:
    """Render a Jinja template against a context.

    Args:
        template: The template string.
        context: The rendering context.

    Returns:
        The rendered string.

    Raises:
        TemplateRenderError: If Jinja2 is not installed or rendering fails.
    """
    if not JINJA_AVAILABLE:
        raise TemplateRenderError(
            template,
            ImportError("jinja2 is not installed. Install it with: pip install jinja2"),
        )

    # The wrapper objects are injected here rather than in build_context so
    # that the context stays a plain, inspectable dict.
    enriched = dict(context)
    enriched["var"] = _VariableView(context.get("__variables__", {}))
    enriched["conn"] = _Namespace(context.get("__connections__", {}))

    try:
        env = Environment(
            loader=BaseLoader(),
            undefined=StrictUndefined,
            keep_trailing_newline=True,
        )
        return env.from_string(template).render(**enriched)
    except Exception as exc:  # noqa: BLE001 - re-raised as TemplateRenderError
        raise TemplateRenderError(template, exc) from exc


class _Namespace:
    """Attribute access over a mapping — models ``conn.my_conn.host``."""

    def __init__(self, values: Mapping[str, Any]) -> None:
        self._values = dict(values)

    def __getattr__(self, item: str) -> Any:
        if item.startswith("_"):
            raise AttributeError(item)
        if item in self._values:
            return self._values[item]
        raise AttributeError(f"no such object: {item!r}")

    def __getitem__(self, item: str) -> Any:
        return self._values[item]

    def __contains__(self, item: str) -> bool:
        return item in self._values

    def __repr__(self) -> str:
        return f"<Namespace {sorted(self._values)}>"


def render_all(
    templates: Mapping[str, str], context: Mapping[str, Any]
) -> dict[str, str]:
    """Render a set of templates.

    Args:
        templates: A mapping of name -> template string.
        context: The rendering context.

    Returns:
        A mapping of name -> rendered string.
    """
    return {name: render_template(text, context) for name, text in templates.items()}
