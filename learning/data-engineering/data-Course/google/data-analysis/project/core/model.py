"""
model.py — the semantic layer of the data analysis course.

A BI tool is not a chart builder. It is a **semantic layer** that sits
between your raw tables and the people asking questions, and this module
is that layer, in pure Python.

Everything here imports nothing outside the standard library. That is
deliberate, and it is the whole premise of the course:

    * Looker Studio, Looker and dbt all implement the *same* ideas —
      a measure is an aggregation with a type, a dimension is a grouping
      key, a join has a relationship and a cardinality, and a model has a
      grain. Learning the ideas from the implementation means you can
      transfer them to whichever tool you are handed.
    * Business logic that lives inside a LookML file is nearly impossible
      to unit-test, because rendering LookML requires the Looker
      application. The same logic in a plain Python module is testable in
      milliseconds.
    * When the logic is pure, `pytest` runs in well under a second with
      no GCP account, no Looker instance and no bill.

Usage:
    from model import (
        Measure,
        Dimension,
        Join,
        Model,
        build_sales_model,
        aggregate,
    )

    model = build_sales_model()
    result = aggregate(model, rows, dimensions=["region"], measures=["revenue"])
    print(result.to_csv())
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

# --------------------------------------------------------------------------
# Measure and dimension types
# --------------------------------------------------------------------------

#: The aggregation functions a measure can use.
AGGREGATIONS = frozenset(
    {"sum", "count", "count_distinct", "avg", "min", "max", "median"}
)

#: How a measure aggregates.
SUM = "sum"
COUNT = "count"
COUNT_DISTINCT = "count_distinct"
AVG = "avg"
MIN = "min"
MAX = "max"

#: The data types a measure can have. The distinction that matters most is
#: ``count`` (a non-additive measure: you cannot sum a count) versus
#: everything else.
COUNT_TYPE = "count"
SUM_TYPE = "sum"
AVERAGE_TYPE = "average"
RATIO_TYPE = "ratio"

#: The relationship types a join can have. The cardinality is the part
#: people get wrong, and it is the part that silently changes a number.
ONE_TO_ONE = "one_to_one"
MANY_TO_ONE = "many_to_one"
ONE_TO_MANY = "one_to_many"
MANY_TO_MANY = "many_to_many"


@dataclass(frozen=True)
class Measure:
    """One aggregate calculation, defined over a single view.

    A measure answers a question *about a number*: total revenue, average
    order value, distinct customers. It is not the same thing as a
    dimension, and mixing them up is the most common modelling mistake in
    BI.

    Attributes:
        name: The snake_case identifier.
        label: The human-readable name shown in the UI.
        type: The measure type — ``sum``, ``count``, ``average`` or
            ``ratio``.
        aggregation: The aggregation function.
        expression: The SQL expression to aggregate.
        description: Optional prose explaining what it measures.
        filters: Optional SQL predicates applied before aggregation.
    """

    name: str
    label: str
    type: str
    aggregation: str
    expression: str
    description: str = ""
    filters: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate the measure.

        Raises:
            ValueError: If the name, type or aggregation is invalid.
        """
        if not re.fullmatch(r"[a-z][a-z0-9_]*", self.name):
            raise ValueError(
                f"measure name {self.name!r} must be snake_case starting "
                f"with a letter"
            )
        if self.aggregation not in AGGREGATIONS:
            raise ValueError(
                f"measure {self.name!r} has unknown aggregation "
                f"{self.aggregation!r}; expected one of {sorted(AGGREGATIONS)}"
            )
        if self.type not in (COUNT_TYPE, SUM_TYPE, AVERAGE_TYPE, RATIO_TYPE):
            raise ValueError(
                f"measure {self.name!r} has unknown type {self.type!r}"
            )
        if self.type == COUNT_TYPE and self.aggregation not in (
            COUNT,
            COUNT_DISTINCT,
        ):
            raise ValueError(
                f"measure {self.name!r} is a count but aggregates with "
                f"{self.aggregation!r}; counts use count or count_distinct"
            )

    @property
    def is_additive(self) -> bool:
        """Whether the measure can be summed across a higher grain.

        A ``count`` cannot: the count of orders in each region summed
        together is the total count of orders, which is only true because
        each order belongs to exactly one region. A ``count_distinct`` of
        customers cannot, because a customer can appear in several
        regions. A ``ratio`` cannot, because averaging an average is not
        the average.

        Returns:
            True when summing the measure across a coarser grain is
            correct.
        """
        if self.aggregation in (COUNT, COUNT_DISTINCT):
            return False
        if self.type == RATIO_TYPE:
            return False
        return True

    @property
    def needs_denominator(self) -> bool:
        """Whether the measure is a ratio over a numerator and denominator.

        Returns:
            True when the measure must be computed as a ratio of two
            aggregates rather than by aggregating a column.
        """
        return self.type == RATIO_TYPE


@dataclass(frozen=True)
class Dimension:
    """One grouping key, defined over a single view.

    A dimension answers a question *about a category*: which region, which
    channel, which month. It has a type, and the type decides how it
    sorts and whether it can be used as a date.

    Attributes:
        name: The snake_case identifier.
        label: The human-readable name shown in the UI.
        type: The dimension type.
        expression: The SQL expression to group by.
        description: Optional prose explaining what it captures.
        timeframe: For a date dimension, the granularities it supports —
            ``raw``, ``day``, ``week``, ``month``, ``quarter``, ``year``.
    """

    name: str
    label: str
    type: str
    expression: str
    description: str = ""
    timeframe: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate the dimension.

        Raises:
            ValueError: If the name or type is invalid.
        """
        if not re.fullmatch(r"[a-z][a-z0-9_]*", self.name):
            raise ValueError(
                f"dimension name {self.name!r} must be snake_case starting "
                f"with a letter"
            )
        if self.type not in ("string", "number", "time", "boolean"):
            raise ValueError(
                f"dimension {self.name!r} has unknown type {self.type!r}"
            )
        if self.timeframe and self.type != "time":
            raise ValueError(
                f"dimension {self.name!r} has a timeframe but is not a time "
                f"dimension"
            )

    @property
    def is_temporal(self) -> bool:
        """Whether the dimension is a date or timestamp.

        Returns:
            True for a time dimension.
        """
        return self.type == "time"


@dataclass(frozen=True)
class Join:
    """One relationship between two models.

    The `relationship` — the cardinality — is the part that matters. A
    `many_to_one` join can be traversed in an explore without changing
    the numbers. A `one_to_many` join **cannot**: the fan-out multiplies
    the rows, and every measure on the far side is silently inflated.

    Attributes:
        name: The join's identifier.
        from_model: The model doing the joining.
        to_model: The model being joined in.
        type: The relationship type.
        foreign_key: The column in ``from_model``.
        primary_key: The column in ``to_model``.
        condition: An optional extra SQL predicate.
        description: Optional prose explaining the relationship.
    """

    name: str
    from_model: str
    to_model: str
    type: str
    foreign_key: str
    primary_key: str
    condition: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        """Validate the join.

        Raises:
            ValueError: If the relationship type is invalid.
        """
        if self.type not in (
            ONE_TO_ONE,
            MANY_TO_ONE,
            ONE_TO_MANY,
            MANY_TO_MANY,
        ):
            raise ValueError(
                f"join {self.name!r} has unknown relationship {self.type!r}"
            )

    @property
    def causes_fan_out(self) -> bool:
        """Whether traversing this join multiplies rows.

        Returns:
            True when the join can inflate the far side's measures.
        """
        return self.type in (ONE_TO_MANY, MANY_TO_MANY)

    @property
    def is_safe_to_traverse(self) -> bool:
        """Whether the join preserves the measure values.

        Returns:
            True when the join does not fan out.
        """
        return not self.causes_fan_out


@dataclass
class Model:
    """One table, its grain, and the measures and dimensions on it.

    The **grain** is the single most important sentence you can write
    about a model: it says what one row represents. "One row per order
    line" and "one row per order" are different grains, and joining them
    without thinking is how a revenue number doubles.

    Attributes:
        name: The model's identifier.
        label: The human-readable name.
        table: The underlying table name.
        sql: An optional SQL expression for a derived model.
        description: What the model represents.
        grain: The grain, in words.
        primary_key: The column that uniquely identifies a row.
        measures: The measures defined on the model.
        dimensions: The dimensions defined on the model.
        joins: The joins defined on the model.
    """

    name: str
    label: str
    table: str
    description: str = ""
    grain: str = ""
    primary_key: str = ""
    sql: str = ""
    measures: list[Measure] = field(default_factory=list)
    dimensions: list[Dimension] = field(default_factory=list)
    joins: list[Join] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate the model's internal consistency.

        Raises:
            ValueError: If a measure or dimension name is duplicated.
        """
        if not re.fullmatch(r"[a-z][a-z0-9_]*", self.name):
            raise ValueError(
                f"model name {self.name!r} must be snake_case starting with "
                f"a letter"
            )
        measure_names = [m.name for m in self.measures]
        if len(measure_names) != len(set(measure_names)):
            raise ValueError(f"model {self.name!r} has duplicate measure names")
        dimension_names = [d.name for d in self.dimensions]
        if len(dimension_names) != len(set(dimension_names)):
            raise ValueError(
                f"model {self.name!r} has duplicate dimension names"
            )

    def measure(self, name: str) -> Measure:
        """Return the measure with the given name.

        Args:
            name: The measure name.

        Returns:
            The measure.

        Raises:
            KeyError: If the model has no such measure.
        """
        for m in self.measures:
            if m.name == name:
                return m
        raise KeyError(f"model {self.name!r} has no measure {name!r}")

    def dimension(self, name: str) -> Dimension:
        """Return the dimension with the given name.

        Args:
            name: The dimension name.

        Returns:
            The dimension.

        Raises:
            KeyError: If the model has no such dimension.
        """
        for d in self.dimensions:
            if d.name == name:
                return d
        raise KeyError(f"model {self.name!r} has no dimension {name!r}")

    def join(self, name: str) -> Join:
        """Return the join with the given name.

        Args:
            name: The join name.

        Returns:
            The join.

        Raises:
            KeyError: If the model has no such join.
        """
        for j in self.joins:
            if j.name == name:
                return j
        raise KeyError(f"model {self.name!r} has no join {name!r}")


@dataclass
class Explore:
    """A named path through the model graph, starting at a base model.

    An explore is what a report author actually picks from a dropdown. It
    encodes which joins are *available* and, critically, which join path
    is the default.

    Attributes:
        name: The explore's identifier.
        label: The human-readable name.
        base_model: The model the explore starts from.
        joins: The joins available from the base model.
        description: What the explore is for.
    """

    name: str
    label: str
    base_model: str
    joins: list[Join] = field(default_factory=list)
    description: str = ""

    def __post_init__(self) -> None:
        """Validate the explore.

        Raises:
            ValueError: If the explore has no base model or no joins.
        """
        if not self.base_model:
            raise ValueError(f"explore {self.name!r} has no base model")
        if not self.joins:
            raise ValueError(f"explore {self.name!r} has no joins")

    def join(self, name: str) -> Join:
        """Return the join with the given name.

        Args:
            name: The join name.

        Returns:
            The join.

        Raises:
            KeyError: If the explore has no such join.
        """
        for j in self.joins:
            if j.name == name:
                return j
        raise KeyError(f"explore {self.name!r} has no join {name!r}")

    @property
    def fan_out_joins(self) -> list[Join]:
        """The joins that would inflate measures if traversed.

        Returns:
            The fan-out joins.
        """
        return [j for j in self.joins if j.causes_fan_out]


# --------------------------------------------------------------------------
# The local BI engine
# --------------------------------------------------------------------------


@dataclass
class ResultRow:
    """One row of a query result.

    Attributes:
        dimensions: The dimension values, keyed by dimension name.
        measures: The measure values, keyed by measure name.
    """

    dimensions: dict[str, Any] = field(default_factory=dict)
    measures: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return the row as a flat dictionary.

        Returns:
            The dimension values followed by the measure values.
        """
        return {**self.dimensions, **self.measures}


@dataclass
class Result:
    """The output of an aggregate query.

    Attributes:
        rows: The result rows.
        columns: The column names in output order.
    """

    rows: list[ResultRow] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)

    def to_csv(self) -> str:
        """Render the result as CSV.

        Returns:
            The CSV text, with a header row.
        """
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer, fieldnames=self.columns, extrasaction="ignore"
        )
        writer.writeheader()
        for row in self.rows:
            writer.writerow(row.to_dict())
        return buffer.getvalue()

    def to_dicts(self) -> list[dict[str, Any]]:
        """Return the rows as a list of dictionaries.

        Returns:
            One dictionary per row.
        """
        return [row.to_dict() for row in self.rows]


def _as_number(value: Any) -> float | None:
    """Coerce a value to a number, or None if it is not numeric.

    Args:
        value: The value to coerce.

    Returns:
        The numeric value, or None.
    """
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").replace("$", ""))
    except ValueError:
        return None


def _round(value: float, places: int = 2) -> float:
    """Round a number to a number of decimal places.

    Args:
        value: The value to round.
        places: The number of decimal places.

    Returns:
        The rounded value.
    """
    factor = 10**places
    return round(value * factor) / factor


def aggregate(
    model: Model,
    rows: Iterable[dict[str, Any]],
    dimensions: Sequence[str] = (),
    measures: Sequence[str] = (),
) -> Result:
    """Aggregate rows according to a model's measures and dimensions.

    This is the local BI engine: it does what an explore does in Looker,
    in about forty lines, so that you can see exactly what the tool is
    doing to your numbers.

    The aggregation handles the three cases that matter:

    * **Additive measures** are summed per group.
    * **Ratios** are computed as a numerator over a denominator, and the
      denominator is re-aggregated per group — never averaged.
    * **Counts** are counted per group.

    Args:
        model: The model whose measures and dimensions to use.
        rows: The rows to aggregate.
        dimensions: The dimension names to group by.
        measures: The measure names to compute.

    Returns:
        The aggregated result, with one row per group.

    Raises:
        KeyError: If a dimension or measure is not on the model.
    """
    if not measures:
        raise KeyError("an aggregate query needs at least one measure")

    for name in dimensions:
        model.dimension(name)
    for name in measures:
        model.measure(name)

    groups: dict[tuple, list[dict[str, Any]]] = {}
    for row in rows:
        key = tuple(_group_value(row, model.dimension(d)) for d in dimensions)
        groups.setdefault(key, []).append(row)

    result_rows: list[ResultRow] = []
    for key in sorted(groups, key=lambda k: tuple(str(v) for v in k)):
        group = groups[key]
        result_row = ResultRow(
            dimensions={
                name: value
                for name, value in zip(dimensions, key)
            }
        )
        for measure_name in measures:
            measure = model.measure(measure_name)
            result_row.measures[measure_name] = _aggregate_measure(
                measure, group, model
            )
        result_rows.append(result_row)

    return Result(
        rows=result_rows,
        columns=list(dimensions) + list(measures),
    )


def _group_value(row: dict[str, Any], dimension: Dimension) -> Any:
    """Extract the grouping value for one dimension from one row.

    Args:
        row: The row.
        dimension: The dimension.

    Returns:
        The value, or None if the row does not carry it.
    """
    if dimension.name in row:
        return row[dimension.name]
    # Fall back to the last segment of the expression, so `orders.created_at`
    # groups on the `created_at` column of a row that carries flat names.
    expression = dimension.expression
    if "." in expression:
        expression = expression.split(".")[-1]
    return row.get(expression)


def _aggregate_measure(
    measure: Measure,
    group: list[dict[str, Any]],
    model: Model,
) -> Any:
    """Compute one measure over one group of rows.

    Args:
        measure: The measure to compute.
        group: The rows in the group.
        model: The owning model.

    Returns:
        The aggregated value.
    """
    if measure.aggregation == COUNT:
        return len(group)

    if measure.aggregation == COUNT_DISTINCT:
        expression = _bare_expression(measure.expression)
        seen = {
            row.get(expression)
            for row in group
            if row.get(expression) is not None
        }
        return len(seen)

    values = [
        _as_number(row.get(_bare_expression(measure.expression)))
        for row in group
    ]
    numbers = [v for v in values if v is not None]

    if measure.needs_denominator:
        return _compute_ratio(measure, group, model)

    if not numbers:
        return 0

    if measure.aggregation == SUM:
        return _round(sum(numbers))
    if measure.aggregation == AVG:
        return _round(sum(numbers) / len(numbers))
    if measure.aggregation == MIN:
        return _round(min(numbers))
    if measure.aggregation == MAX:
        return _round(max(numbers))
    if measure.aggregation == MEDIAN:
        ordered = sorted(numbers)
        middle = len(ordered) // 2
        if len(ordered) % 2 == 1:
            return _round(ordered[middle])
        return _round((ordered[middle - 1] + ordered[middle]) / 2)
    return 0


def _compute_ratio(
    measure: Measure,
    group: list[dict[str, Any]],
    model: Model,
) -> Any:
    """Compute a ratio measure as numerator over denominator.

    The denominator is re-aggregated over the same group. It is never
    the average of per-row ratios — that is the mistake that turns a
    conversion rate into a meaningless number.

    Args:
        measure: The ratio measure.
        group: The rows in the group.
        model: The owning model.

    Returns:
        The ratio, or None when the denominator is zero.
    """
    numerator = measure.expression
    denominator = measure.filters[0] if measure.filters else ""
    if not denominator:
        raise ValueError(
            f"ratio measure {measure.name!r} has no denominator expression"
        )

    numerator_values = [
        _as_number(row.get(_bare_expression(numerator))) for row in group
    ]
    denominator_values = [
        _as_number(row.get(_bare_expression(denominator))) for row in group
    ]

    num = sum(v for v in numerator_values if v is not None)
    den = sum(v for v in denominator_values if v is not None)
    if den == 0:
        return None
    return _round(num / den, 4)


def _bare_expression(expression: str) -> str:
    """Strip any table prefix from a SQL expression.

    Args:
        expression: The expression, e.g. ``orders.total_amount``.

    Returns:
        The bare column name, e.g. ``total_amount``.
    """
    stripped = expression.strip()
    if "(" in stripped:
        return stripped
    if "." in stripped:
        return stripped.split(".")[-1]
    return stripped


def build_sales_model() -> Model:
    """Build the orders model the course uses throughout.

    Returns:
        The orders model, with its measures, dimensions and joins.
    """
    return Model(
        name="orders",
        label="Orders",
        table="analytics.orders",
        description=(
            "One row per order line. Note the grain: a single order with "
            "three lines appears three times."
        ),
        grain="one row per order line",
        primary_key="line_id",
        measures=[
            Measure(
                name="total_revenue",
                label="Total Revenue",
                type=SUM_TYPE,
                aggregation=SUM,
                expression="total_amount",
                description="Sum of order line revenue.",
            ),
            Measure(
                name="order_count",
                label="Order Count",
                type=COUNT_TYPE,
                aggregation=COUNT,
                expression="order_id",
                description=(
                    "Number of order lines. To count orders rather than "
                    "lines, use count_distinct on order_id."
                ),
            ),
            Measure(
                name="distinct_orders",
                label="Distinct Orders",
                type=COUNT_TYPE,
                aggregation=COUNT_DISTINCT,
                expression="order_id",
                description="Number of unique orders.",
            ),
            Measure(
                name="average_order_value",
                label="Average Order Value",
                type=AVERAGE_TYPE,
                aggregation=AVG,
                expression="total_amount",
                description="Average revenue per order line.",
            ),
            Measure(
                name="gross_margin",
                label="Gross Margin",
                type=RATIO_TYPE,
                aggregation=SUM,
                expression="margin_amount",
                description="Margin over revenue.",
                filters=("total_amount",),
            ),
        ],
        dimensions=[
            Dimension(
                name="order_id",
                label="Order ID",
                type="string",
                expression="order_id",
                description=(
                    "The order identifier. NOT unique — one order has many "
                    "lines. Use line_id to identify a row."
                ),
            ),
            Dimension(
                name="line_id",
                label="Order Line ID",
                type="string",
                expression="line_id",
                description="The unique order-line identifier. The grain.",
            ),
            Dimension(
                name="customer_id",
                label="Customer",
                type="string",
                expression="customer_id",
                description="The customer who placed the order.",
            ),
            Dimension(
                name="region",
                label="Region",
                type="string",
                expression="region",
                description="Sales region: EMEA, AMER, APAC or LATAM.",
            ),
            Dimension(
                name="channel",
                label="Channel",
                type="string",
                expression="channel",
                description="Sales channel: web, app, store or partner.",
            ),
            Dimension(
                name="status",
                label="Status",
                type="string",
                expression="status",
                description="Order status.",
            ),
            Dimension(
                name="created_at",
                label="Order Date",
                type="time",
                expression="created_at",
                description="When the order was placed.",
                timeframe=("raw", "day", "week", "month", "quarter", "year"),
            ),
            Dimension(
                name="product_category",
                label="Product Category",
                type="string",
                expression="product_category",
                description="The category of the product on the line.",
            ),
        ],
        joins=[
            Join(
                name="customers",
                from_model="orders",
                to_model="customers",
                type=MANY_TO_ONE,
                foreign_key="customer_id",
                primary_key="customer_id",
                description=(
                    "Many order lines belong to one customer. Safe to "
                    "traverse: it does not fan out."
                ),
            ),
            Join(
                name="products",
                from_model="orders",
                to_model="products",
                type=MANY_TO_ONE,
                foreign_key="product_id",
                primary_key="product_id",
                description=(
                    "Many order lines reference one product. Safe to "
                    "traverse."
                ),
            ),
        ],
    )


def build_customer_model() -> Model:
    """Build the customers model.

    Returns:
        The customers model.
    """
    return Model(
        name="customers",
        label="Customers",
        table="analytics.customers",
        description="One row per customer.",
        grain="one row per customer",
        primary_key="customer_id",
        measures=[
            Measure(
                name="customer_count",
                label="Customers",
                type=COUNT_TYPE,
                aggregation=COUNT_DISTINCT,
                expression="customer_id",
                description="Number of customers.",
            ),
            Measure(
                name="lifetime_value",
                label="Lifetime Value",
                type=SUM_TYPE,
                aggregation=SUM,
                expression="lifetime_value",
                description="Total spend recorded on the customer record.",
            ),
        ],
        dimensions=[
            Dimension(
                name="customer_id",
                label="Customer ID",
                type="string",
                expression="customer_id",
                description="The unique customer identifier. The grain of this table.",
            ),
            Dimension(
                name="customer_segment",
                label="Segment",
                type="string",
                expression="segment",
                description="The customer's marketing segment.",
            ),
            Dimension(
                name="country",
                label="Country",
                type="string",
                expression="country",
                description="The customer's country. A conformed dimension — the same meaning in every fact table that joins it.",
            ),
            Dimension(
                name="signup_date",
                label="Signup Date",
                type="time",
                expression="signup_date",
                description=(
                    "When the customer signed up. Note this is the current "
                    "value only — the table is SCD Type 1, so a segment "
                    "change overwrites rather than adding a row."
                ),
                timeframe=("raw", "day", "month", "year"),
            ),
        ],
        joins=[
            Join(
                name="orders",
                from_model="customers",
                to_model="orders",
                type=ONE_TO_MANY,
                foreign_key="customer_id",
                primary_key="customer_id",
                description=(
                    "One customer has many orders. Traversing this "
                    "fan-outs the order lines — and therefore the "
                    "revenue — unless the measure is a distinct count."
                ),
            ),
        ],
    )


def build_product_model() -> Model:
    """Build the products model.

    Returns:
        The products model.
    """
    return Model(
        name="products",
        label="Products",
        table="analytics.products",
        description="One row per product.",
        grain="one row per product",
        primary_key="product_id",
        measures=[
            Measure(
                name="product_count",
                label="Products",
                type=COUNT_TYPE,
                aggregation=COUNT_DISTINCT,
                expression="product_id",
                description="Number of distinct products. Non-additive — the same product appears in many order lines.",
            ),
            Measure(
                name="list_price",
                label="List Price",
                type=AVERAGE_TYPE,
                aggregation=AVG,
                expression="list_price",
                description=(
                    "Average list price across the product table. "
                    "Non-additive — never sum it."
                ),
            ),
        ],
        dimensions=[
            Dimension(
                name="product_id",
                label="Product ID",
                type="string",
                expression="product_id",
                description="The unique product identifier. The grain of this table.",
            ),
            Dimension(
                name="product_category",
                label="Category",
                type="string",
                expression="category",
                description="The product's catalogue category.",
            ),
            Dimension(
                name="supplier",
                label="Supplier",
                type="string",
                expression="supplier",
                description="The supplier who provides the product.",
            ),
        ],
    )


def build_explores() -> list[Explore]:
    """Build the explores the course uses.

    Returns:
        The explores.
    """
    return [
        Explore(
            name="orders",
            label="Orders",
            base_model="orders",
            description="The order-line explore the reports are built on.",
            joins=[
                Join(
                    name="customers",
                    from_model="orders",
                    to_model="customers",
                    type=MANY_TO_ONE,
                    foreign_key="customer_id",
                    primary_key="customer_id",
                ),
                Join(
                    name="products",
                    from_model="orders",
                    to_model="products",
                    type=MANY_TO_ONE,
                    foreign_key="product_id",
                    primary_key="product_id",
                ),
            ],
        ),
        Explore(
            name="customers",
            label="Customers",
            base_model="customers",
            description="A customer explore, for segmentation questions.",
            joins=[
                Join(
                    name="orders",
                    from_model="customers",
                    to_model="orders",
                    type=ONE_TO_MANY,
                    foreign_key="customer_id",
                    primary_key="customer_id",
                    description=(
                        "One customer has many orders. Traversing this "
                        "fan-outs the order lines — and therefore the "
                        "revenue — unless the measure is a distinct count."
                    ),
                ),
            ],
        ),
    ]
