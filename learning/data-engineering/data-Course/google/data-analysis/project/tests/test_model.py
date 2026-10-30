"""Tests for the semantic layer — measures, dimensions, joins and the grain."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

CORE = Path(__file__).resolve().parent.parent / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from model import (  # noqa: E402
    COUNT,
    COUNT_DISTINCT,
    COUNT_TYPE,
    MANY_TO_MANY,
    MANY_TO_ONE,
    ONE_TO_MANY,
    ONE_TO_ONE,
    RATIO_TYPE,
    SUM,
    SUM_TYPE,
    Dimension,
    Explore,
    Join,
    Measure,
    Model,
    aggregate,
    build_customer_model,
    build_explores,
    build_product_model,
    build_sales_model,
)


# --------------------------------------------------------------------------
# Measure
# --------------------------------------------------------------------------


def test_measure_rejects_a_non_snake_case_name():
    """A measure named `Total Revenue` cannot be referenced in SQL."""
    with pytest.raises(ValueError, match="snake_case"):
        Measure(
            name="Total Revenue",
            label="Total Revenue",
            type=SUM_TYPE,
            aggregation=SUM,
            expression="total_amount",
        )


def test_measure_rejects_an_unknown_aggregation():
    """An unknown aggregation is a configuration error."""
    with pytest.raises(ValueError, match="unknown aggregation"):
        Measure(
            name="total_revenue",
            label="Total Revenue",
            type=SUM_TYPE,
            aggregation="totalise",
            expression="total_amount",
        )


def test_a_count_measure_must_aggregate_with_a_count():
    """A count typed measure cannot sum a column."""
    with pytest.raises(ValueError, match="counts use count"):
        Measure(
            name="order_count",
            label="Order Count",
            type=COUNT_TYPE,
            aggregation=SUM,
            expression="order_id",
        )


def test_a_sum_measure_is_additive():
    """A sum can be added up across a coarser grain."""
    measure = Measure(
        name="total_revenue",
        label="Total Revenue",
        type=SUM_TYPE,
        aggregation=SUM,
        expression="total_amount",
    )
    assert measure.is_additive
    assert not measure.needs_denominator


def test_a_count_measure_is_not_additive():
    """A count cannot be summed across a coarser grain."""
    measure = Measure(
        name="order_count",
        label="Order Count",
        type=COUNT_TYPE,
        aggregation=COUNT,
        expression="order_id",
    )
    assert not measure.is_additive


def test_a_count_distinct_measure_is_not_additive():
    """A distinct count cannot be summed across a coarser grain — a
    customer can appear in more than one region."""
    measure = Measure(
        name="distinct_orders",
        label="Distinct Orders",
        type=COUNT_TYPE,
        aggregation=COUNT_DISTINCT,
        expression="order_id",
    )
    assert not measure.is_additive


def test_a_ratio_measure_is_not_additive():
    """A ratio cannot be summed — averaging an average is not the average."""
    measure = Measure(
        name="gross_margin",
        label="Gross Margin",
        type=RATIO_TYPE,
        aggregation=SUM,
        expression="margin_amount",
        filters=("total_amount",),
    )
    assert not measure.is_additive
    assert measure.needs_denominator


# --------------------------------------------------------------------------
# Dimension
# --------------------------------------------------------------------------


def test_dimension_rejects_an_unknown_type():
    """A dimension must have a known type."""
    with pytest.raises(ValueError, match="unknown type"):
        Dimension(
            name="created_at",
            label="Order Date",
            type="timestamp-ish",
            expression="created_at",
        )


def test_a_timeframe_requires_a_time_dimension():
    """A string dimension cannot have timeframes."""
    with pytest.raises(ValueError, match="not a time dimension"):
        Dimension(
            name="region",
            label="Region",
            type="string",
            expression="region",
            timeframe=("day",),
        )


def test_a_time_dimension_is_temporal():
    """A time dimension reports itself as temporal."""
    dimension = Dimension(
        name="created_at",
        label="Order Date",
        type="time",
        expression="created_at",
        timeframe=("day", "month"),
    )
    assert dimension.is_temporal


# --------------------------------------------------------------------------
# Join
# --------------------------------------------------------------------------


def test_join_rejects_an_unknown_relationship():
    """The relationship must be one of the four cardinalities."""
    with pytest.raises(ValueError, match="unknown relationship"):
        Join(
            name="customers",
            from_model="orders",
            to_model="customers",
            type="some_to_one",
            foreign_key="customer_id",
            primary_key="customer_id",
        )


def test_a_many_to_one_join_does_not_fan_out():
    """Traversing a many-to-one join is safe."""
    join = Join(
        name="customers",
        from_model="orders",
        to_model="customers",
        type=MANY_TO_ONE,
        foreign_key="customer_id",
        primary_key="customer_id",
    )
    assert not join.causes_fan_out
    assert join.is_safe_to_traverse


def test_a_one_to_many_join_fans_out():
    """Traversing a one-to-many join multiplies the rows."""
    join = Join(
        name="orders",
        from_model="customers",
        to_model="orders",
        type=ONE_TO_MANY,
        foreign_key="customer_id",
        primary_key="order_id",
    )
    assert join.causes_fan_out
    assert not join.is_safe_to_traverse


def test_a_many_to_many_join_fans_out():
    """Traversing a many-to-many join multiplies the rows."""
    join = Join(
        name="tags",
        from_model="orders",
        to_model="tags",
        type=MANY_TO_MANY,
        foreign_key="order_id",
        primary_key="order_id",
    )
    assert join.causes_fan_out


def test_a_one_to_one_join_does_not_fan_out():
    """A one-to-one join is safe."""
    join = Join(
        name="profile",
        from_model="customers",
        to_model="profiles",
        type=ONE_TO_ONE,
        foreign_key="customer_id",
        primary_key="customer_id",
    )
    assert not join.causes_fan_out


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------


def test_model_rejects_duplicate_measure_names():
    """Two measures with the same name would make the field ambiguous."""
    with pytest.raises(ValueError, match="duplicate measure names"):
        Model(
            name="orders",
            label="Orders",
            table="analytics.orders",
            measures=[
                Measure(
                    name="total_revenue",
                    label="A",
                    type=SUM_TYPE,
                    aggregation=SUM,
                    expression="a",
                ),
                Measure(
                    name="total_revenue",
                    label="B",
                    type=SUM_TYPE,
                    aggregation=SUM,
                    expression="b",
                ),
            ],
        )


def test_model_rejects_duplicate_dimension_names():
    """Two dimensions with the same name would make the field ambiguous."""
    with pytest.raises(ValueError, match="duplicate dimension names"):
        Model(
            name="orders",
            label="Orders",
            table="analytics.orders",
            dimensions=[
                Dimension(
                    name="region", label="A", type="string", expression="a"
                ),
                Dimension(
                    name="region", label="B", type="string", expression="b"
                ),
            ],
        )


def test_model_lookups_raise_on_unknown_names():
    """Looking up a field that does not exist is a KeyError."""
    model = build_sales_model()
    with pytest.raises(KeyError):
        model.measure("nonexistent")
    with pytest.raises(KeyError):
        model.dimension("nonexistent")
    with pytest.raises(KeyError):
        model.join("nonexistent")


def test_the_sales_model_declares_its_grain():
    """The grain is the most important sentence about a model."""
    model = build_sales_model()
    assert model.grain == "one row per order line"
    assert model.primary_key == "line_id"


# --------------------------------------------------------------------------
# Explore
# --------------------------------------------------------------------------


def test_an_explore_needs_a_base_model():
    """An explore with no base model is meaningless."""
    with pytest.raises(ValueError, match="no base model"):
        Explore(name="orders", label="Orders", base_model="")


def test_an_explore_needs_at_least_one_join():
    """An explore with no joins is just a model."""
    with pytest.raises(ValueError, match="no joins"):
        Explore(name="orders", label="Orders", base_model="orders", joins=[])


def test_an_explore_reports_its_fan_out_joins():
    """The customers explore has a fan-out join and must say so."""
    explores = {e.name: e for e in build_explores()}
    assert explores["orders"].fan_out_joins == []
    assert [j.name for j in explores["customers"].fan_out_joins] == ["orders"]


# --------------------------------------------------------------------------
# Aggregation — the local BI engine
# --------------------------------------------------------------------------

ROWS = [
    {
        "order_id": "o1",
        "line_id": "l1",
        "customer_id": "c1",
        "region": "EMEA",
        "total_amount": 100.0,
        "margin_amount": 40.0,
    },
    {
        "order_id": "o1",
        "line_id": "l2",
        "customer_id": "c1",
        "region": "EMEA",
        "total_amount": 50.0,
        "margin_amount": 20.0,
    },
    {
        "order_id": "o2",
        "line_id": "l3",
        "customer_id": "c2",
        "region": "AMER",
        "total_amount": 200.0,
        "margin_amount": 80.0,
    },
]


def test_aggregate_sums_an_additive_measure():
    """Revenue is summed per group."""
    model = build_sales_model()
    result = aggregate(model, ROWS, ["region"], ["total_revenue"])
    values = {r.dimensions["region"]: r.measures["total_revenue"] for r in result.rows}
    assert values == {"AMER": 200.0, "EMEA": 150.0}


def test_aggregate_counts_distinct_values():
    """Two lines in one order count as one order."""
    model = build_sales_model()
    result = aggregate(model, ROWS, ["region"], ["distinct_orders"])
    values = {r.dimensions["region"]: r.measures["distinct_orders"] for r in result.rows}
    assert values == {"AMER": 1, "EMEA": 1}


def test_aggregate_counts_rows_for_a_plain_count():
    """A plain count counts lines, not orders."""
    model = build_sales_model()
    result = aggregate(model, ROWS, ["region"], ["order_count"])
    values = {r.dimensions["region"]: r.measures["order_count"] for r in result.rows}
    assert values == {"AMER": 1, "EMEA": 2}


def test_aggregate_computes_a_ratio_over_its_denominator():
    """The ratio is margin over revenue, re-aggregated per group."""
    model = build_sales_model()
    result = aggregate(model, ROWS, ["region"], ["gross_margin"])
    values = {r.dimensions["region"]: r.measures["gross_margin"] for r in result.rows}
    assert values == {"AMER": 0.4, "EMEA": 0.4}


def test_a_ratio_is_not_the_average_of_per_row_ratios():
    """The classic mistake: averaging per-row ratios.

    Row 1 is a $900 sale with an $810 margin (ratio 0.9). Row 2 is a
    $100 sale with a $10 margin (ratio 0.1). The average of the two
    per-row ratios is 0.5. The correct answer — total margin over total
    revenue — is 820 / 1000 = 0.82. The two differ, and the difference
    is exactly the error this module exists to prevent.
    """
    rows = [
        {"region": "EMEA", "total_amount": 900.0, "margin_amount": 810.0},
        {"region": "EMEA", "total_amount": 100.0, "margin_amount": 10.0},
    ]
    model = build_sales_model()
    result = aggregate(model, rows, ["region"], ["gross_margin"])

    correct = result.rows[0].measures["gross_margin"]
    assert correct == 0.82

    average_of_ratios = (0.9 + 0.1) / 2
    assert correct != average_of_ratios


def test_a_ratio_with_a_zero_denominator_is_none():
    """A ratio over zero is undefined, not infinite."""
    rows = [{"region": "EMEA", "total_amount": 0.0, "margin_amount": 0.0}]
    model = build_sales_model()
    result = aggregate(model, rows, ["region"], ["gross_margin"])
    assert result.rows[0].measures["gross_margin"] is None


def test_aggregate_rejects_an_unknown_dimension():
    """A query for a field that does not exist must fail loudly."""
    model = build_sales_model()
    with pytest.raises(KeyError):
        aggregate(model, ROWS, ["nope"], ["total_revenue"])


def test_aggregate_rejects_an_unknown_measure():
    """A query for a measure that does not exist must fail loudly."""
    model = build_sales_model()
    with pytest.raises(KeyError):
        aggregate(model, ROWS, ["region"], ["nope"])


def test_aggregate_requires_at_least_one_measure():
    """A query with no measure is a dimension listing, not a query."""
    model = build_sales_model()
    with pytest.raises(KeyError, match="at least one measure"):
        aggregate(model, ROWS, ["region"], [])


def test_aggregate_without_dimensions_returns_one_row():
    """No dimensions means the whole table is one group."""
    model = build_sales_model()
    result = aggregate(model, ROWS, [], ["total_revenue"])
    assert len(result.rows) == 1
    assert result.rows[0].measures["total_revenue"] == 350.0


def test_aggregate_ignores_null_numbers():
    """A null measure value does not become zero in an average."""
    rows = [
        {"region": "EMEA", "total_amount": 100.0},
        {"region": "EMEA", "total_amount": None},
    ]
    model = build_sales_model()
    result = aggregate(model, rows, ["region"], ["average_order_value"])
    assert result.rows[0].measures["average_order_value"] == 100.0


def test_result_renders_csv():
    """The result renders as CSV with a header row."""
    model = build_sales_model()
    result = aggregate(model, ROWS, ["region"], ["total_revenue"])
    text = result.to_csv()
    assert text.splitlines()[0] == "region,total_revenue"
    assert "EMEA,150.0" in text


def test_result_rows_carry_dimensions_then_measures():
    """A row's flat dictionary has dimensions first."""
    model = build_sales_model()
    result = aggregate(model, ROWS, ["region"], ["total_revenue"])
    row = result.to_dicts()[0]
    assert list(row) == ["region", "total_revenue"]


# --------------------------------------------------------------------------
# The builders
# --------------------------------------------------------------------------


def test_the_sales_model_has_the_expected_measures():
    """The sales model carries the measures the chapters use."""
    model = build_sales_model()
    names = {m.name for m in model.measures}
    assert {
        "total_revenue",
        "order_count",
        "distinct_orders",
        "average_order_value",
        "gross_margin",
    } <= names


def test_the_sales_model_has_the_expected_dimensions():
    """The sales model carries the dimensions the chapters use."""
    model = build_sales_model()
    names = {d.name for d in model.dimensions}
    assert {
        "order_id",
        "line_id",
        "customer_id",
        "region",
        "channel",
        "status",
        "created_at",
        "product_category",
    } <= names


def test_the_created_at_dimension_supports_the_timeframes():
    """The date dimension supports the grains the chapters use."""
    model = build_sales_model()
    dimension = model.dimension("created_at")
    assert dimension.is_temporal
    assert "month" in dimension.timeframe


def test_the_customer_model_is_one_row_per_customer():
    """The customer model's grain is one row per customer."""
    model = build_customer_model()
    assert model.grain == "one row per customer"
    assert model.primary_key == "customer_id"


def test_the_product_model_is_one_row_per_product():
    """The product model's grain is one row per product."""
    model = build_product_model()
    assert model.grain == "one row per product"
    assert model.primary_key == "product_id"


def test_the_orders_explore_has_no_fan_out_join():
    """The orders explore is safe — both joins are many-to-one."""
    explores = {e.name: e for e in build_explores()}
    assert explores["orders"].fan_out_joins == []
