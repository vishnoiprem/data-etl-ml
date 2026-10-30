"""
lookml.py — a small LookML reader and writer.

LookML is the language Looker uses to describe a semantic layer: the
models, their explores, their measures, dimensions and joins. Looker
Studio does not use LookML — it has a UI — but the **concepts** are the
same, and every Looker concept has a Looker Studio equivalent:

    ==========================  ==================================
    Looker (LookML)             Looker Studio
    ==========================  ==================================
    `view` + `explore`          a data source (or a *blended* source)
    `measure`                   a metric
    `dimension`                 a dimension
    `join` + `relationship`     a join + a relationship type
    `sql:` / `derive:`          the calculated field's SQL
    `timeframe:`                the date grain dropdown
    `filters:`                  the filter's scope
    ==========================  ==================================

So learning LookML teaches you Looker Studio, and the reverse is also
true: a data modeler who has only used the Looker Studio UI usually
does not know *why* the relationship type matters.

This module implements a **pragmatic subset** of LookML:

    * `view` blocks with `sql`, `label`, `description`, `dimension`,
      `measure`, `join` and `explore` blocks;
    * `dimension`, `measure`, `join` and `explore` parameter parsing;
    * `{{ }}` and `{{ table.column }}` reference detection, so a broken
      reference is caught at build time rather than at render time.

It also **generates** LookML from a :class:`~model.Model`, which is the
useful direction: the local semantic layer in ``model.py`` is the source
of truth, and this module renders it into the file a Looker developer
would actually commit.

Everything is pure standard library. Usage:

    from lookml import parse_view, render_view, find_broken_references

    text = render_view(build_sales_model())
    view = parse_view(text)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from model import (
    AVERAGE_TYPE,
    COUNT,
    COUNT_DISTINCT,
    COUNT_TYPE,
    MANY_TO_MANY,
    MANY_TO_ONE,
    ONE_TO_MANY,
    ONE_TO_ONE,
    RATIO_TYPE,
    SUM_TYPE,
    Dimension,
    Explore,
    Join,
    Measure,
    Model,
)

#: The LookML relationship names, mapped to the course's relationship
#: constants. Looker spells them without underscores.
RELATIONSHIP_MAP = {
    "one_to_one": ONE_TO_ONE,
    "many_to_one": MANY_TO_ONE,
    "one_to_many": ONE_TO_MANY,
    "many_to_many": MANY_TO_MANY,
}

#: The reverse map, for rendering.
RELATIONSHIP_NAMES = {value: key for key, value in RELATIONSHIP_MAP.items()}

#: How a Looker measure type maps onto the course's measure types.
MEASURE_TYPE_MAP = {
    "count": COUNT_TYPE,
    "sum": SUM_TYPE,
    "average": SUM_TYPE,
    "ratio": RATIO_TYPE,
}

#: The reverse map, for rendering.
MEASURE_TYPE_NAMES = {
    COUNT_TYPE: "count",
    SUM_TYPE: "sum",
    AVERAGE_TYPE: "average",
    RATIO_TYPE: "ratio",
}

#: The Looker aggregations the renderer emits.
AGGREGATION_NAMES = {
    COUNT: "count",
    COUNT_DISTINCT: "count_distinct",
    "sum": "sum",
    "avg": "average",
    "min": "min",
    "max": "max",
    "median": "median",
}


@dataclass
class LookMLParameter:
    """One parsed LookML parameter.

    Attributes:
        name: The parameter name.
        value: The parameter value, with whitespace stripped.
    """

    name: str
    value: str

    @property
    def is_list(self) -> bool:
        """Whether the value is a comma-separated list.

        Returns:
            True when the value contains a comma.
        """
        return "," in self.value

    def as_list(self) -> list[str]:
        """Return the value as a list.

        Returns:
            The comma-separated items, stripped and non-empty.
        """
        return [item.strip() for item in self.value.split(",") if item.strip()]


@dataclass
class LookMLDimension:
    """A parsed ``dimension`` block.

    Attributes:
        name: The dimension name.
        label: The label.
        type: The dimension type.
        sql: The SQL expression.
        description: The description.
        timeframe: The supported timeframes.
        hidden: Whether the dimension is hidden from the field picker.
        primary_key: Whether the dimension is the primary key.
    """

    name: str
    label: str = ""
    type: str = "string"
    sql: str = ""
    description: str = ""
    timeframe: tuple[str, ...] = ()
    hidden: bool = False
    primary_key: bool = False


@dataclass
class LookMLMeasure:
    """A parsed ``measure`` block.

    Attributes:
        name: The measure name.
        label: The label.
        type: The measure type.
        sql: The SQL expression.
        description: The description.
        filters: The measure's filters.
        hidden: Whether the measure is hidden.
    """

    name: str
    label: str = ""
    type: str = "sum"
    sql: str = ""
    description: str = ""
    filters: tuple[str, ...] = ()
    hidden: bool = False


@dataclass
class LookMLJoin:
    """A parsed ``join`` block.

    Attributes:
        name: The join name.
        type: The relationship type.
        sql_on: The join condition.
        description: The description.
    """

    name: str
    type: str = "many_to_one"
    sql_on: str = ""
    description: str = ""


@dataclass
class LookMLExplore:
    """A parsed ``explore`` block.

    Attributes:
        name: The explore name.
        label: The label.
        description: The description.
        joins: The joins declared inside the explore.
    """

    name: str
    label: str = ""
    description: str = ""
    joins: list[LookMLJoin] = field(default_factory=list)


@dataclass
class LookMLView:
    """A parsed ``view`` block.

    Attributes:
        name: The view name.
        label: The label.
        description: The description.
        sql: The view's SQL.
        dimensions: The dimensions.
        measures: The measures.
        joins: The joins.
        explores: The explores.
    """

    name: str
    label: str = ""
    description: str = ""
    sql: str = ""
    dimensions: list[LookMLDimension] = field(default_factory=list)
    measures: list[LookMLMeasure] = field(default_factory=list)
    joins: list[LookMLJoin] = field(default_factory=list)
    explores: list[LookMLExplore] = field(default_factory=list)

    def dimension(self, name: str) -> LookMLDimension:
        """Return a dimension by name.

        Args:
            name: The dimension name.

        Returns:
            The dimension.

        Raises:
            KeyError: If the view has no such dimension.
        """
        for d in self.dimensions:
            if d.name == name:
                return d
        raise KeyError(f"view {self.name!r} has no dimension {name!r}")

    def measure(self, name: str) -> LookMLMeasure:
        """Return a measure by name.

        Args:
            name: The measure name.

        Returns:
            The measure.

        Raises:
            KeyError: If the view has no such measure.
        """
        for m in self.measures:
            if m.name == name:
                return m
        raise KeyError(f"view {self.name!r} has no measure {name!r}")


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

#: Matches a `parameter: value` line.
_PARAMETER_RE = re.compile(r"^\s*([a-z_]+)\s*:\s*(.*)$")

#: Matches the start of a nested block, e.g. `dimension: order_id {`.
_BLOCK_START_RE = re.compile(
    r"^\s*(dimension|measure|join|explore|derived_column|map)\s*:\s*"
    r"([A-Za-z0-9_]+)\s*\{"
)

#: Matches the start of a block with no name, e.g. `explore: orders {`.
_NAMELESS_BLOCK_RE = re.compile(
    r"^\s*(explore)\s*:\s*([A-Za-z0-9_]*)\s*\{"
)


def parse_view(text: str) -> LookMLView:
    """Parse one LookML ``view`` block into a :class:`LookMLView`.

    The parser is deliberately forgiving about whitespace and indentation
    and strict about structure. It understands the subset the course
    uses; it is not a complete LookML implementation.

    Args:
        text: The LookML source of one view.

    Returns:
        The parsed view.

    Raises:
        ValueError: If the text contains no ``view`` block.
    """
    lines = text.splitlines()
    view: LookMLView | None = None
    stack: list[tuple[str, str, list[str]]] = []
    context: dict[str, Any] = {}

    for raw_line in lines:
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        stripped = line.strip()

        if stripped.startswith("view:"):
            if view is None:
                view = LookMLView(name=stripped.split(":", 1)[1].strip().rstrip("{").strip())
                context = {"view": view}
            continue

        if view is None:
            continue

        match = _BLOCK_START_RE.match(line)
        if match:
            kind, name = match.group(1), match.group(2)
            stack.append((kind, name, []))
            continue

        match = _NAMELESS_BLOCK_RE.match(line)
        if match:
            kind, name = match.group(1), match.group(2)
            stack.append((kind, name, []))
            continue

        if stripped == "}":
            if not stack:
                continue
            kind, name, params = stack.pop()
            _close_block(context, stack, kind, name, params)
            continue

        if stack:
            stack[-1][2].append(stripped)
            continue

        match = _PARAMETER_RE.match(line)
        if match:
            key = match.group(1)
            value = _unquote(match.group(2))
            if key == "label":
                view.label = value
            elif key == "description":
                view.description = value
            elif key == "sql":
                view.sql = value
            elif key == "explore":
                view.explores.append(
                    LookMLExplore(name=value.rstrip("{").strip())
                )

    if view is None:
        raise ValueError("no `view:` block found in the LookML source")

    return view


def _close_block(
    context: dict[str, Any],
    stack: list[tuple[str, str, list[str]]],
    kind: str,
    name: str,
    params: list[str],
) -> None:
    """Close a nested block and attach it to its parent.

    Args:
        context: The parse context, holding the view.
        stack: The remaining open blocks.
        kind: The block kind.
        name: The block name.
        params: The parameter lines inside the block.

    Returns:
        None.
    """
    view: LookMLView = context["view"]
    parsed = _parse_parameters(params)

    if kind == "dimension":
        view.dimensions.append(
            LookMLDimension(
                name=name,
                label=parsed.get("label", ""),
                type=parsed.get("type", "string"),
                sql=parsed.get("sql", ""),
                description=parsed.get("description", ""),
                timeframe=tuple(
                    item.strip()
                    for item in parsed.get("timeframe", "").split(",")
                    if item.strip()
                ),
                hidden=parsed.get("hidden", "").lower() == "yes",
                primary_key=parsed.get("primary_key", "").lower() == "yes",
            )
        )
    elif kind == "measure":
        view.measures.append(
            LookMLMeasure(
                name=name,
                label=parsed.get("label", ""),
                type=parsed.get("type", "sum"),
                sql=parsed.get("sql", ""),
                description=parsed.get("description", ""),
                filters=tuple(
                    item.strip()
                    for item in parsed.get("filters", "").split(",")
                    if item.strip()
                ),
                hidden=parsed.get("hidden", "").lower() == "yes",
            )
        )
    elif kind == "join":
        view.joins.append(
            LookMLJoin(
                name=name,
                type=parsed.get("relationship", "many_to_one"),
                sql_on=parsed.get("sql_on", ""),
                description=parsed.get("description", ""),
            )
        )
    elif kind == "explore":
        explore = LookMLExplore(
            name=name,
            label=parsed.get("label", ""),
            description=parsed.get("description", ""),
        )
        for join_name in parsed.get("join", "").split(","):
            cleaned = join_name.strip()
            if cleaned:
                explore.joins.append(
                    LookMLJoin(name=cleaned, type="many_to_one")
                )
        view.explores.append(explore)


def _unquote(value: str) -> str:
    """Strip the surrounding quotes from a LookML string value.

    LookML quotes every string: ``label: "Orders"``. A parser that keeps
    the quotes produces a label of ``"Orders"`` — with the quote marks
    visible in the UI.

    Args:
        value: The raw value.

    Returns:
        The value without its surrounding quotes.
    """
    text = value.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        return text[1:-1]
    return text


def _parse_parameters(lines: Iterable[str]) -> dict[str, str]:
    """Parse ``key: value`` lines into a dictionary.

    A repeated key accumulates into a comma-separated list, which is how
    LookML handles repeated parameters such as ``filters``.

    Args:
        lines: The parameter lines.

    Returns:
        The parsed parameters.
    """
    parsed: dict[str, str] = {}
    for line in lines:
        match = _PARAMETER_RE.match(line)
        if not match:
            continue
        key = match.group(1)
        value = _unquote(match.group(2))
        if key in parsed:
            parsed[key] = f"{parsed[key]}, {value}"
        else:
            parsed[key] = value
    return parsed


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def _quote(value: str) -> str:
    """Quote a LookML string value.

    Args:
        value: The value.

    Returns:
        The quoted value.
    """
    return f'"{value}"'


def _indent(text: str, spaces: int) -> str:
    """Indent every line of a block of text.

    Args:
        text: The text.
        spaces: The number of spaces.

    Returns:
        The indented text.
    """
    pad = " " * spaces
    return "\n".join(f"{pad}{line}" if line.strip() else line for line in text.splitlines())


def render_measure(measure: Measure) -> str:
    """Render a measure as a LookML ``measure`` block.

    Args:
        measure: The measure.

    Returns:
        The LookML text.
    """
    lines = [
        f"  measure: {measure.name} {{",
        f"    label: {_quote(measure.label)}",
    ]
    if measure.type == COUNT_TYPE:
        lines.append("    type: count")
    elif measure.type == RATIO_TYPE:
        lines.append("    type: ratio")
    elif measure.type == "average":
        lines.append("    type: average")
    else:
        lines.append("    type: sum")
    if measure.expression:
        lines.append(f"    sql: {_quote(measure.expression)}")
    if measure.filters:
        lines.append(
            f"    filters: {_quote(', '.join(measure.filters))}"
        )
    if measure.description:
        lines.append(f"    description: {_quote(measure.description)}")
    lines.append("  }")
    return "\n".join(lines)


def render_dimension(dimension: Dimension) -> str:
    """Render a dimension as a LookML ``dimension`` block.

    Args:
        dimension: The dimension.

    Returns:
        The LookML text.
    """
    lines = [
        f"  dimension: {dimension.name} {{",
        f"    label: {_quote(dimension.label)}",
        f"    type: {dimension.type}",
    ]
    if dimension.expression:
        lines.append(f"    sql: {_quote(dimension.expression)}")
    if dimension.timeframe:
        lines.append(
            f"    timeframe: {_quote(', '.join(dimension.timeframe))}"
        )
    if dimension.description:
        lines.append(f"    description: {_quote(dimension.description)}")
    lines.append("  }")
    return "\n".join(lines)


def render_join(join: Join) -> str:
    """Render a join as a LookML ``join`` block.

    Args:
        join: The join.

    Returns:
        The LookML text.
    """
    relationship = RELATIONSHIP_NAMES.get(join.type, "many_to_one")
    condition = (
        f"{join.from_model}.{join.foreign_key} = "
        f"{join.to_model}.{join.primary_key}"
    )
    lines = [
        f"  join: {join.name} {{",
        f"    relationship: {relationship}",
        f"    sql_on: {_quote(condition)}",
    ]
    if join.description:
        lines.append(f"    description: {_quote(join.description)}")
    lines.append("  }")
    return "\n".join(lines)


def render_view(model: Model) -> str:
    """Render a model as a LookML ``view`` block.

    Args:
        model: The model.

    Returns:
        The LookML text.
    """
    lines = [
        f"view: {model.name} {{",
        f"  label: {_quote(model.label)}",
    ]
    if model.grain:
        lines.append(f"  description: {_quote(model.description)}")
        lines.append(f"  # Grain: {model.grain}")
    if model.table:
        lines.append(f'  sql: {_quote(f"select * from {model.table}")};')
    lines.append("")
    for dimension in model.dimensions:
        lines.append(render_dimension(dimension))
        lines.append("")
    for measure in model.measures:
        lines.append(render_measure(measure))
        lines.append("")
    for join in model.joins:
        lines.append(render_join(join))
        lines.append("")
    while lines and not lines[-1]:
        lines.pop()
    lines.append("}")
    return "\n".join(lines)


def render_explore(explore: Explore) -> str:
    """Render an explore as a LookML ``explore`` block.

    Args:
        explore: The explore.

    Returns:
        The LookML text.
    """
    lines = [
        f"explore: {explore.name} {{",
        f"  label: {_quote(explore.label)}",
    ]
    if explore.description:
        lines.append(f"  description: {_quote(explore.description)}")
    if explore.joins:
        lines.append(
            f"  join: {_quote(', '.join(j.name for j in explore.joins))}"
        )
    lines.append("}")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Reference checking
# --------------------------------------------------------------------------

#: Matches a LookML reference. Looker writes field references as
#: ``${view.field}``; the ``{{ view.field }}`` form appears in Liquid
#: templates and in some older LookML. Both are matched, so a hand-written
#: view is checked whichever style it uses.
_REFERENCE_RE = re.compile(
    r"\$\{\s*([A-Za-z0-9_.\s]+?)\s*\}"
    r"|\{\{\s*([A-Za-z0-9_.\s]+?)\s*\}\}"
)


def find_references(text: str) -> list[str]:
    """Find every field reference in a LookML source.

    Args:
        text: The LookML source.

    Returns:
        The reference names, without the delimiters.
    """
    references: list[str] = []
    for match in _REFERENCE_RE.finditer(text):
        name = match.group(1) if match.group(1) is not None else match.group(2)
        references.append(name.strip())
    return references


def find_broken_references(
    text: str,
    available: Iterable[str],
) -> list[str]:
    """Find references that do not resolve to an available field.

    A ``${ customers.name }`` reference to a view that does not exist is
    a **build error** in Looker, not a runtime error — which is good,
    because it means the mistake cannot reach a dashboard. Catching it
    locally, before the Looker developer ever runs ``lookml-validate``,
    is the point of this function.

    Looker resolves a reference in one of three ways, and all three are
    accepted here:

    * ``view.field`` — a field of another view;
    * ``view`` — the view itself (used by ``${orders}`` in a ``sql:``);
    * ``field`` — a field of the view the reference appears in.

    Args:
        text: The LookML source.
        available: The names that resolve — typically
            ``view.field`` pairs.

    Returns:
        The broken references, in the order they appear.
    """
    known = {name.lower() for name in available}

    # The set of view names, and the set of bare field names, so that a
    # `${orders}` or a `${total_revenue}` resolves the way Looker resolves it.
    view_names = {name.split(".", 1)[0] for name in known}
    field_names = {name.split(".", 1)[1] for name in known if "." in name}

    broken: list[str] = []
    for reference in find_references(text):
        lowered = reference.lower()
        if lowered in known or lowered in view_names or lowered in field_names:
            continue
        broken.append(reference)
    return broken


def collect_available_fields(models: Iterable[Model]) -> list[str]:
    """Collect every resolvable ``view.field`` reference for a set of models.

    Args:
        models: The models.

    Returns:
        The reference names.
    """
    available: list[str] = []
    for model in models:
        for dimension in model.dimensions:
            available.append(f"{model.name}.{dimension.name}")
        for measure in model.measures:
            available.append(f"{model.name}.{measure.name}")
    return available
