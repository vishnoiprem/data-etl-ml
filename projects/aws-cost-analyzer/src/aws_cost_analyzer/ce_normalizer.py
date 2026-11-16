"""Normalising Cost Explorer's nested response into flat cost records.

AWS returns a deeply nested structure:

```
ResultsByTime[]                        → one per period
  .TimePeriod.Start / .TimePeriod.End  → the period
  .Estimated                           → whether the period is a projection
  .Groups[]                            → one per group combination
    .Keys[]                            → POSITIONAL, matching GroupDefinitions
    .Metrics["UnblendedCost"]
      .Amount                          → a STRING
```

Six rules, two of them landmines.

**The end date is exclusive.** ``TimePeriod.End`` is "up to and
including 2017-04-30 but not including 2017-05-01". The caller sends an
already-exclusive end; this module records the period as AWS reported
it, so ``period_end`` is the exclusive bound.

**Group keys are positional.** ``Groups[].Keys[i]`` corresponds to
``GroupDefinitions[i]`` — *by position*, not by any name in the payload.
The payload does not say which dimension ``Keys[0]`` is. So the
normalizer is given the group definitions and keeps them alongside the
record; flattening them into a dict would silently lose the mapping and
make a tag value indistinguishable from a service name.

**Amounts are strings.** An unparseable amount is a *recorded error*,
never coerced to ``0.0``. Coercing it would erase a cost without
telling anyone — and a missing month looks exactly like a cheap month.

A normalizer that drops a group under-counts the bill, and every
downstream finding is then wrong in a way no unit test catches. This is
why the test suite asserts exact row counts and payload equality
against recorded fixtures.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from .models import CostRecord


@dataclass(slots=True)
class NormalizationResult:
    """What one normalizer run produced, and what it could not."""

    records: list[CostRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    periods_seen: list[str] = field(default_factory=list)
    estimated_periods: list[str] = field(default_factory=list)

    @property
    def total_amount(self) -> float:
        return sum(r.amount for r in self.records)

    def by_period(self) -> dict[str, list[CostRecord]]:
        """Records grouped by their period label."""
        grouped: dict[str, list[CostRecord]] = {}
        for record in self.records:
            grouped.setdefault(record.period_label, []).append(record)
        return grouped


def normalize_cost_and_usage(
    payload: dict[str, Any],
    *,
    region: str = "",
    group_definitions: list[dict[str, str]] | None = None,
    metric: str = "UnblendedCost",
    granularity: str = "MONTHLY",
    default_service: str = "",
) -> NormalizationResult:
    """Turn one Cost Explorer page into flat records.

    ``group_definitions`` is the ``GroupBy`` list that was sent with the
    request. It is what makes ``record.group`` interpretable: the
    definition at position *i* describes the key at position *i*.
    """
    result = NormalizationResult()

    for time_row in payload.get("ResultsByTime", []) or []:
        period = time_row.get("TimePeriod", {}) or {}
        start_raw = period.get("Start")
        end_raw = period.get("End")
        if not start_raw or not end_raw:
            result.errors.append(f"period without Start/End: {period!r}")
            continue

        try:
            period_start = date.fromisoformat(start_raw)
            period_end = date.fromisoformat(end_raw)
        except ValueError as exc:
            result.errors.append(f"unparseable period {start_raw}..{end_raw}: {exc}")
            continue

        label = period_start.strftime("%Y-%m")
        if label not in result.periods_seen:
            result.periods_seen.append(label)

        estimated = bool(time_row.get("Estimated", False))
        if estimated and label not in result.estimated_periods:
            result.estimated_periods.append(label)

        for group in time_row.get("Groups", []) or []:
            keys = list(group.get("Keys", []) or [])
            metrics = group.get("Metrics", {}) or {}

            metric_block = metrics.get(metric)
            if metric_block is None:
                # The requested metric was not returned for this group.
                continue

            amount_raw = metric_block.get("Amount")
            try:
                amount = float(amount_raw)
            except (TypeError, ValueError):
                result.errors.append(
                    f"unparseable amount {amount_raw!r} for group {keys!r} in {label}"
                )
                continue

            service = _service_from_keys(keys, group_definitions, default_service)

            result.records.append(
                CostRecord(
                    period_start=period_start,
                    period_end=period_end,
                    granularity=granularity,
                    service=service,
                    region=region,
                    group=tuple(keys),
                    amount=amount,
                    metric=metric,
                    estimated=estimated,
                )
            )

    return result


def _service_from_keys(
    keys: list[str],
    group_definitions: list[dict[str, str]] | None,
    default_service: str,
) -> str:
    """The service a record belongs to.

    When the first group dimension is ``SERVICE``, the first key *is*
    the service. Otherwise the service is unknown and the caller-supplied
    default is used — guessing would be worse than admitting it.
    """
    if not group_definitions:
        return default_service or (keys[0] if keys else "")

    first = group_definitions[0]
    if first.get("Type") == "DIMENSION" and first.get("Key") == "SERVICE":
        return keys[0] if keys else default_service
    return default_service


def describe_group(
    keys: list[str],
    group_definitions: list[dict[str, str]] | None,
) -> str:
    """A human label for a group, e.g. ``service=S3 tag=Data``.

    The mapping is positional, so this is the only place the tuple's
    elements get their names back.
    """
    if not group_definitions:
        return "/".join(keys) if keys else "(no group)"

    parts: list[str] = []
    for index, key in enumerate(keys):
        if index < len(group_definitions):
            definition = group_definitions[index]
            parts.append(f"{definition.get('Key', '?').lower()}={key}")
        else:
            parts.append(f"?={key}")
    return " ".join(parts)


# --------------------------------------------------------------------------- #
# Pagination
# --------------------------------------------------------------------------- #


def paginate(
    fetch_page,
    *,
    max_pages: int = 100,
) -> list[dict[str, Any]]:
    """Collect every page of a Cost Explorer response.

    The pagination loop belongs to the *fetcher*, not the normalizer.
    The normalizer stays pure per page: it converts one payload into
    records and has no opinion about how many pages there were. That
    separation is what lets the normalizer be tested against single
    recorded pages.

    ``fetch_page`` takes an optional page token and returns the raw
    payload.
    """
    pages: list[dict[str, Any]] = []
    token: str | None = None

    for _ in range(max_pages):
        payload = fetch_page(token)
        pages.append(payload)

        next_token = payload.get("NextPageToken")
        if not next_token:
            return pages
        token = next_token

    raise RuntimeError(f"pagination did not terminate within {max_pages} pages")


def merge_pages(pages: list[dict[str, Any]]) -> dict[str, Any]:
    """Combine several Cost Explorer pages into one payload.

    The ``ResultsByTime`` lists are concatenated. The group definitions
    are taken from the first page — they describe the *request*, and
    every page of the same request shares them.
    """
    merged: dict[str, Any] = {"ResultsByTime": []}
    for page in pages:
        merged["ResultsByTime"].extend(page.get("ResultsByTime", []) or [])
        if "GroupDefinitions" not in merged and page.get("GroupDefinitions"):
            merged["GroupDefinitions"] = page["GroupDefinitions"]
        if "DimensionValues" not in merged and page.get("DimensionValues"):
            merged["DimensionValues"] = page["DimensionValues"]
    return merged


# --------------------------------------------------------------------------- #
# The with-resources variant
# --------------------------------------------------------------------------- #


def normalize_with_resources(
    payload: dict[str, Any],
    *,
    region: str = "",
    group_definitions: list[dict[str, str]] | None = None,
    metric: str = "UnblendedCost",
    granularity: str = "MONTHLY",
) -> NormalizationResult:
    """Normalise a ``GetCostAndUsageWithResources`` response.

    The shape is the same as the plain one, except that each group
    carries a ``Resources`` list — the S3 buckets (or resources) that
    make up that group. Those become one record per resource, which is
    what makes per-bucket attribution possible.
    """
    result = NormalizationResult()

    for time_row in payload.get("ResultsByTime", []) or []:
        period = time_row.get("TimePeriod", {}) or {}
        start_raw = period.get("Start")
        end_raw = period.get("End")
        if not start_raw or not end_raw:
            result.errors.append(f"period without Start/End: {period!r}")
            continue

        try:
            period_start = date.fromisoformat(start_raw)
            period_end = date.fromisoformat(end_raw)
        except ValueError as exc:
            result.errors.append(f"unparseable period {start_raw}..{end_raw}: {exc}")
            continue

        label = period_start.strftime("%Y-%m")
        if label not in result.periods_seen:
            result.periods_seen.append(label)

        estimated = bool(time_row.get("Estimated", False))
        if estimated and label not in result.estimated_periods:
            result.estimated_periods.append(label)

        for group in time_row.get("Groups", []) or []:
            keys = list(group.get("Keys", []) or [])
            metrics = group.get("Metrics", {}) or {}
            metric_block = metrics.get(metric)
            if metric_block is None:
                continue

            try:
                amount = float(metric_block.get("Amount"))
            except (TypeError, ValueError):
                result.errors.append(
                    f"unparseable amount {metric_block.get('Amount')!r} "
                    f"for group {keys!r} in {label}"
                )
                continue

            service = _service_from_keys(keys, group_definitions, "Amazon Simple Storage Service")

            resources = group.get("Resources", []) or []
            if not resources:
                result.records.append(
                    CostRecord(
                        period_start=period_start,
                        period_end=period_end,
                        granularity=granularity,
                        service=service,
                        region=region,
                        group=tuple(keys),
                        amount=amount,
                        metric=metric,
                        estimated=estimated,
                    )
                )
                continue

            resource_keys = list(resources[0].get("Keys", []) or [])
            resource_id = resource_keys[0] if resource_keys else ""

            result.records.append(
                CostRecord(
                    period_start=period_start,
                    period_end=period_end,
                    granularity=granularity,
                    service=service,
                    region=region,
                    group=tuple(keys) + (resource_id,),
                    amount=amount,
                    metric=metric,
                    estimated=estimated,
                )
            )

    return result


# --------------------------------------------------------------------------- #
# Serialisation
# --------------------------------------------------------------------------- #


def records_to_json(records: list[CostRecord], result: NormalizationResult | None = None) -> str:
    """Serialise records for a snapshot file."""
    payload: dict[str, Any] = {"records": [r.to_dict() for r in records]}
    if result is not None:
        payload["errors"] = list(result.errors)
        payload["periods_seen"] = list(result.periods_seen)
        payload["estimated_periods"] = list(result.estimated_periods)
    return json.dumps(payload, indent=2, sort_keys=True)


def records_from_json(raw: str) -> list[CostRecord]:
    """Read records back out of a snapshot file."""
    data = json.loads(raw)
    return [CostRecord.from_dict(row) for row in data.get("records", [])]
