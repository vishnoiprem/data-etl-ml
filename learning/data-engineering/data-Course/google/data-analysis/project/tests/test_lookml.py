"""Tests for the LookML reader and writer."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

CORE = Path(__file__).resolve().parent.parent / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from lookml import (  # noqa: E402
    collect_available_fields,
    find_broken_references,
    find_references,
    parse_view,
    render_explore,
    render_view,
)
from model import (  # noqa: E402
    MANY_TO_ONE,
    ONE_TO_MANY,
    build_customer_model,
    build_explores,
    build_sales_model,
)

SAMPLE = """
view: orders {
  label: "Orders"
  description: "One row per order line."

  dimension: order_id {
    label: "Order ID"
    type: string
    sql: "order_id"
    description: "The order identifier."
  }

  dimension: created_at {
    label: "Order Date"
    type: time
    sql: "created_at"
    timeframe: "raw, day, month"
  }

  measure: total_revenue {
    label: "Total Revenue"
    type: sum
    sql: "total_amount"
    description: "Sum of order line revenue."
  }

  join: customers {
    relationship: many_to_one
    sql_on: "orders.customer_id = customers.customer_id"
    description: "Many order lines to one customer."
  }

  explore: orders {
    label: "Orders"
    join: "customers"
  }
}
"""


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------


def test_parse_view_reads_the_name_and_label():
    """The view's name and label come from the source."""
    view = parse_view(SAMPLE)
    assert view.name == "orders"
    assert view.label == "Orders"
    assert view.description == "One row per order line."


def test_parse_view_reads_the_dimensions():
    """Every dimension is parsed with its parameters."""
    view = parse_view(SAMPLE)
    assert [d.name for d in view.dimensions] == ["order_id", "created_at"]
    dimension = view.dimension("order_id")
    assert dimension.label == "Order ID"
    assert dimension.type == "string"
    assert dimension.sql == "order_id"


def test_parse_view_reads_the_timeframes():
    """A timeframe list is parsed into a tuple."""
    view = parse_view(SAMPLE)
    dimension = view.dimension("created_at")
    assert dimension.timeframe == ("raw", "day", "month")
    assert dimension.type == "time"


def test_parse_view_reads_the_measures():
    """Every measure is parsed with its parameters."""
    view = parse_view(SAMPLE)
    assert [m.name for m in view.measures] == ["total_revenue"]
    measure = view.measure("total_revenue")
    assert measure.type == "sum"
    assert measure.sql == "total_amount"


def test_parse_view_reads_the_joins():
    """A join's relationship is parsed."""
    view = parse_view(SAMPLE)
    assert len(view.joins) == 1
    join = view.joins[0]
    assert join.name == "customers"
    assert join.type == "many_to_one"
    assert "customer_id" in join.sql_on


def test_parse_view_reads_the_explores():
    """An explore's joins are parsed."""
    view = parse_view(SAMPLE)
    assert len(view.explores) == 1
    explore = view.explores[0]
    assert explore.name == "orders"
    assert explore.label == "Orders"
    assert [j.name for j in explore.joins] == ["customers"]


def test_parse_view_raises_without_a_view_block():
    """Source with no `view:` is not a view."""
    with pytest.raises(ValueError, match="no `view:` block"):
        parse_view("explore: orders {\n  label: \"Orders\"\n}\n")


def test_parse_view_ignores_comments():
    """A commented-out line is not parsed."""
    view = parse_view(
        """
view: orders {
  label: "Orders"
  # dimension: commented_out {
  #   label: "Nope"
  # }
}
"""
    )
    assert view.dimensions == []


def test_looking_up_a_missing_dimension_raises():
    """A lookup of a field that does not exist is a KeyError."""
    view = parse_view(SAMPLE)
    with pytest.raises(KeyError):
        view.dimension("nope")
    with pytest.raises(KeyError):
        view.measure("nope")


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def test_render_view_produces_a_view_block():
    """The rendered LookML is a `view` block."""
    text = render_view(build_sales_model())
    assert text.startswith("view: orders {")
    assert text.rstrip().endswith("}")


def test_render_view_includes_every_dimension_and_measure():
    """Every field in the model appears in the rendered LookML."""
    model = build_sales_model()
    text = render_view(model)
    for dimension in model.dimensions:
        assert f"dimension: {dimension.name} {{" in text
    for measure in model.measures:
        assert f"measure: {measure.name} {{" in text


def test_render_view_records_the_grain():
    """The grain is the sentence that matters, so it is in the output."""
    text = render_view(build_sales_model())
    assert "Grain: one row per order line" in text


def test_render_view_writes_the_relationship_type():
    """The relationship type is rendered the way Looker spells it."""
    model = build_sales_model()
    text = render_view(model)
    assert "relationship: many_to_one" in text


def test_render_view_round_trips_through_the_parser():
    """What the writer produces, the reader can read back.

    This is the property that makes the local semantic layer useful: the
    Python model is the source of truth, and the LookML file is a
    rendering of it, so the two can never drift apart silently.
    """
    model = build_sales_model()
    view = parse_view(render_view(model))

    assert view.name == model.name
    assert view.label == model.label
    assert {d.name for d in view.dimensions} == {
        d.name for d in model.dimensions
    }
    assert {m.name for m in view.measures} == {m.name for m in model.measures}


def test_render_view_round_trips_the_measure_types():
    """A measure's type survives the round trip."""
    model = build_sales_model()
    view = parse_view(render_view(model))
    assert view.measure("total_revenue").type == "sum"
    assert view.measure("order_count").type == "count"


def test_render_explore_produces_an_explore_block():
    """An explore renders as an `explore` block with its joins."""
    explores = {e.name: e for e in build_explores()}
    text = render_explore(explores["orders"])
    assert text.startswith("explore: orders {")
    assert 'join: "customers, products"' in text


# --------------------------------------------------------------------------
# References
# --------------------------------------------------------------------------


def test_find_references_finds_lookml_references():
    """A `{{ reference }}` is found."""
    text = 'sql: "{{ customers.name }} as customer_name"'
    assert find_references(text) == ["customers.name"]


def test_find_references_ignores_text_without_braces():
    """Ordinary prose has no references."""
    assert find_references("sql: customers.name") == []


def test_find_broken_references_reports_the_unknown_ones():
    """A reference to a field that does not exist is broken."""
    text = (
        'sql: "{{ orders.order_id }}"\n'
        'sql: "{{ orders.nope }}"\n'
        'sql: "{{ ghost.name }}"'
    )
    broken = find_broken_references(
        text, ["orders.order_id", "customers.customer_id"]
    )
    assert broken == ["orders.nope", "ghost.name"]


def test_find_broken_references_is_empty_for_good_lookml():
    """Valid LookML has no broken references."""
    text = (
        'sql: "{{ orders.order_id }}"\n'
        'sql: "{{ customers.customer_segment }}"'
    )
    available = collect_available_fields(
        [build_sales_model(), build_customer_model()]
    )
    assert find_broken_references(text, available) == []


def test_collect_available_fields_lists_view_field_pairs():
    """Every dimension and measure is addressable as `view.field`."""
    available = collect_available_fields([build_sales_model()])
    assert "orders.order_id" in available
    assert "orders.total_revenue" in available


def test_the_shipped_lookml_file_parses():
    """The LookML file the project ships is valid.

    This is the check that keeps the generated file honest — a Looker
    developer who clones the repository gets LookML that parses, with
    the relationship types the chapters claim.
    """
    path = (
        Path(__file__).resolve().parent.parent / "lookml" /
        "ecommerce.model.lookml"
    )
    assert path.exists(), "project/lookml/ecommerce.model.lookml is missing"

    text = path.read_text(encoding="utf-8")
    assert "view: orders {" in text
    assert "view: customers {" in text
    assert "view: products {" in text
    assert "explore: orders {" in text
    assert "relationship: many_to_one" in text


def test_the_shipped_lookml_file_has_the_fan_out_join():
    """The customers explore's fan-out join is declared as one_to_many."""
    path = (
        Path(__file__).resolve().parent.parent / "lookml" /
        "ecommerce.model.lookml"
    )
    text = path.read_text(encoding="utf-8")
    assert "relationship: one_to_many" in text
