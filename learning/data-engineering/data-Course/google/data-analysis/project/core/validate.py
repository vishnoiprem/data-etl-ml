"""
validate.py — the data validation gate.

A dashboard is a promise. "Revenue is up 12% this quarter" is a promise
that some number, computed some way, means something. The promise
breaks quietly:

* a **fan-out join** doubles a revenue number and nobody notices,
  because the chart still looks like a chart;
* a **missing dimension value** silently drops rows out of a total;
* a **late-arriving fact** means yesterday's number changes after
  yesterday's dashboard was read;
* a **schema change** removes a column and the metric goes to zero —
  which looks like a business event, not a bug.

This module is the gate that catches those before a number reaches a
slide. It runs four families of checks:

    * **Grain** — is the primary key actually unique?
    * **Referential** — do the foreign keys resolve?
    * **Completeness** — are the required fields populated?
    * **Freshness** — is the data recent enough to be believed?

Everything is pure standard library. Usage:

    from validate import validate_dataset, ValidationReport

    report = validate_dataset(rows, model, required=["order_id"])
    print(report.to_text())
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

#: The severities a finding can have.
ERROR = "ERROR"
WARNING = "WARNING"
INFO = "INFO"


@dataclass(frozen=True)
class Finding:
    """One validation finding.

    Attributes:
        severity: The severity — ``ERROR``, ``WARNING`` or ``INFO``.
        code: A short machine-readable code.
        message: The human-readable message.
        count: How many rows the finding affects.
    """

    severity: str
    code: str
    message: str
    count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return the finding as a dictionary.

        Returns:
            The finding's fields.
        """
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "count": self.count,
        }


@dataclass
class ValidationReport:
    """The result of a validation run.

    Attributes:
        findings: The findings.
        rows_checked: The number of rows checked.
        source: What was validated.
    """

    findings: list[Finding] = field(default_factory=list)
    rows_checked: int = 0
    source: str = ""

    def add(
        self,
        severity: str,
        code: str,
        message: str,
        count: int = 0,
    ) -> None:
        """Record a finding.

        Args:
            severity: The severity.
            code: The machine-readable code.
            message: The message.
            count: The number of rows affected.

        Returns:
            None.
        """
        self.findings.append(
            Finding(
                severity=severity, code=code, message=message, count=count
            )
        )

    def by_severity(self, severity: str) -> list[Finding]:
        """Return the findings with a given severity.

        Args:
            severity: The severity.

        Returns:
            The matching findings.
        """
        return [f for f in self.findings if f.severity == severity]

    @property
    def errors(self) -> list[Finding]:
        """The error findings.

        Returns:
            The errors.
        """
        return self.by_severity(ERROR)

    @property
    def warnings(self) -> list[Finding]:
        """The warning findings.

        Returns:
            The warnings.
        """
        return self.by_severity(WARNING)

    @property
    def passed(self) -> bool:
        """Whether the validation passed.

        A validation passes when there are no errors. Warnings do not
        fail the run — a dashboard can legitimately have missing values
        in a field nobody reports on.

        Returns:
            True when there are no errors.
        """
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        """Return the report as a dictionary.

        Returns:
            The report's fields.
        """
        return {
            "source": self.source,
            "rows_checked": self.rows_checked,
            "passed": self.passed,
            "findings": [f.to_dict() for f in self.findings],
        }

    def to_text(self) -> str:
        """Render the report as human-readable text.

        Returns:
            The text.
        """
        lines = [
            "Validation report",
            "----------------------------------------------------",
            f"  source            : {self.source or '(unnamed)'}",
            f"  rows checked      : {self.rows_checked}",
            f"  result            : {'PASS' if self.passed else 'FAIL'}",
        ]
        if self.findings:
            lines.append("  findings:")
            for finding in self.findings:
                suffix = f" ({finding.count} rows)" if finding.count else ""
                lines.append(
                    f"    [{finding.severity:7}] {finding.code}: "
                    f"{finding.message}{suffix}"
                )
        else:
            lines.append("  findings: none")
        return "\n".join(lines)


def check_grain(
    rows: Sequence[dict[str, Any]],
    primary_key: str,
    report: ValidationReport | None = None,
) -> ValidationReport:
    """Check that a table's primary key is unique.

    A duplicated primary key is the single most consequential thing that
    can be wrong with a fact table. Every measure over it is inflated,
    and the inflation is proportional to how often the row repeats — so
    it looks like growth.

    Args:
        rows: The rows.
        primary_key: The primary key column.
        report: An existing report to add to. A new one is created when
            omitted.

    Returns:
        The report.
    """
    result = report if report is not None else ValidationReport()

    seen: dict[Any, int] = {}
    null_count = 0
    for row in rows:
        value = row.get(primary_key)
        if value is None or value == "":
            null_count += 1
            continue
        seen[value] = seen.get(value, 0) + 1

    duplicated = {key: count for key, count in seen.items() if count > 1}
    if duplicated:
        result.add(
            ERROR,
            "grain.not_unique",
            (
                f"primary key {primary_key!r} is not unique: "
                f"{len(duplicated)} value(s) repeat. Every measure over "
                f"this table is inflated."
            ),
            count=sum(duplicated.values()) - len(duplicated),
        )
    if null_count:
        result.add(
            ERROR,
            "grain.null_key",
            f"primary key {primary_key!r} is null or empty on some rows",
            count=null_count,
        )
    if not duplicated and not null_count and rows:
        result.add(
            INFO,
            "grain.ok",
            f"primary key {primary_key!r} is unique and populated",
            count=len(rows),
        )
    return result


def check_referential_integrity(
    rows: Sequence[dict[str, Any]],
    foreign_key: str,
    lookup_rows: Sequence[dict[str, Any]],
    lookup_key: str,
    report: ValidationReport | None = None,
) -> ValidationReport:
    """Check that foreign keys resolve to a row in the lookup table.

    An unresolved foreign key is usually a **timing** problem: the fact
    arrived before the dimension row did. In a left-join BI tool it
    produces a blank label, and the row still counts towards the total —
    so the total is right and the breakdown is wrong. That combination
    is worse than either being wrong alone, because nobody checks the
    parts.

    Args:
        rows: The fact rows.
        foreign_key: The foreign key column in the fact rows.
        lookup_rows: The lookup rows.
        lookup_key: The key column in the lookup rows.
        report: An existing report to add to.

    Returns:
        The report.
    """
    result = report if report is not None else ValidationReport()
    result.rows_checked = len(rows)

    known = {
        row.get(lookup_key)
        for row in lookup_rows
        if row.get(lookup_key) is not None
    }
    unresolved: dict[Any, int] = {}
    for row in rows:
        value = row.get(foreign_key)
        if value is None or value == "":
            continue
        if value not in known:
            unresolved[value] = unresolved.get(value, 0) + 1

    if unresolved:
        result.add(
            ERROR,
            "referential.unresolved",
            (
                f"foreign key {foreign_key!r} has {len(unresolved)} value(s) "
                f"with no matching {lookup_key!r}. Those rows will show a "
                f"blank label but still count towards totals."
            ),
            count=sum(unresolved.values()),
        )
    return result


def check_completeness(
    rows: Sequence[dict[str, Any]],
    required: Iterable[str],
    report: ValidationReport | None = None,
) -> ValidationReport:
    """Check that required fields are populated.

    Args:
        rows: The rows.
        required: The field names that must be populated.
        report: An existing report to add to.

    Returns:
        The report.
    """
    result = report if report is not None else ValidationReport()
    result.rows_checked = len(rows)

    for field_name in required:
        missing = sum(
            1
            for row in rows
            if row.get(field_name) is None or row.get(field_name) == ""
        )
        if missing:
            severity = ERROR if field_name.endswith("_id") else WARNING
            result.add(
                severity,
                "completeness.missing",
                f"field {field_name!r} is empty on some rows",
                count=missing,
            )
    return result


def check_freshness(
    rows: Sequence[dict[str, Any]],
    date_field: str,
    max_age_days: int = 2,
    today: Any = None,
    report: ValidationReport | None = None,
) -> ValidationReport:
    """Check that the newest row is recent enough to be believable.

    A stale pipeline is the most common cause of a "why did revenue
    drop?" question, and the answer is usually that it did not drop —
    the extract stopped.

    Args:
        rows: The rows.
        date_field: The date field.
        max_age_days: The maximum acceptable age of the newest row.
        today: The date to measure against. Defaults to today.
        report: An existing report to add to.

    Returns:
        The report.
    """
    result = report if report is not None else ValidationReport()

    from date_helpers import parse_date  # noqa: PLC0415

    if today is None:
        from datetime import date as date_type  # noqa: PLC0415

        today = date_type.today()

    newest: Any = None
    for row in rows:
        value = row.get(date_field)
        if value is None or value == "":
            continue
        try:
            parsed = parse_date(value)
        except ValueError:
            continue
        if newest is None or parsed > newest:
            newest = parsed

    if newest is None:
        result.add(
            WARNING,
            "freshness.no_dates",
            (
                f"no parseable value in {date_field!r}; cannot check "
                f"freshness"
            ),
        )
        return result

    age = (parse_date(today) - newest).days
    if age > max_age_days:
        result.add(
            ERROR,
            "freshness.stale",
            (
                f"newest row in {date_field!r} is {age} day(s) old; "
                f"the limit is {max_age_days}. The numbers are not "
                f"current — say so on the dashboard."
            ),
            count=1,
        )
    else:
        result.add(
            INFO,
            "freshness.ok",
            f"newest row in {date_field!r} is {age} day(s) old",
            count=1,
        )
    return result


def check_no_negative_revenue(
    rows: Sequence[dict[str, Any]],
    field_name: str = "total_amount",
    report: ValidationReport | None = None,
) -> ValidationReport:
    """Check for negative values in a revenue field.

    A negative revenue row is legitimate — a refund, a credit note. But
    it is also the single most common sign of a **sign-flip bug**: a
    join that duplicated the fact table and subtracted the copies, or a
    currency conversion applied in the wrong direction.

    Args:
        rows: The rows.
        field_name: The field to check.
        report: An existing report to add to.

    Returns:
        The report.
    """
    result = report if report is not None else ValidationReport()

    negatives = 0
    for row in rows:
        value = row.get(field_name)
        if isinstance(value, (int, float)) and value < 0:
            negatives += 1

    if negatives:
        result.add(
            WARNING,
            "value.negative",
            (
                f"{negatives} row(s) have a negative {field_name!r}. "
                f"Legitimate for refunds; suspicious for a sign-flip bug."
            ),
            count=negatives,
        )
    return result


def validate_dataset(
    rows: Sequence[dict[str, Any]],
    model: Any = None,
    required: Iterable[str] = (),
    max_age_days: int = 2,
    today: Any = None,
    source: str = "",
) -> ValidationReport:
    """Run every applicable check over a dataset.

    Args:
        rows: The rows.
        model: The model whose primary key and date dimension to use.
        required: Extra required field names.
        max_age_days: The freshness limit.
        today: The date to measure freshness against.
        source: A label for what is being validated.

    Returns:
        The report.
    """
    report = ValidationReport(rows_checked=len(rows), source=source)

    if model is not None:
        primary_key = getattr(model, "primary_key", "")
        if primary_key:
            check_grain(rows, primary_key, report)

        date_dimensions = [
            d for d in getattr(model, "dimensions", []) if d.is_temporal
        ]
        if date_dimensions:
            check_freshness(
                rows,
                date_dimensions[0].expression,
                max_age_days=max_age_days,
                today=today,
                report=report,
            )

    check_completeness(rows, required, report)
    check_no_negative_revenue(rows, report=report)
    return report
