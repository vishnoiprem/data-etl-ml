"""Fan-out helpers: split work so the DAG can parallelise.

The functions here are pure and import nothing from Airflow, so the
fan-out logic can be unit tested without a scheduler and reused by the
local runner.
"""
from __future__ import annotations

from pipeline_logic import summarise_by_region


def regions_to_process(summary: dict[str, dict[str, float]]) -> list[str]:
    """Return the regions that produced revenue, sorted.

    Args:
        summary: The output of `summarise_by_region`.

    Returns:
        A sorted list of region codes.
    """
    return sorted(
        region for region, bucket in summary.items() if bucket["order_count"] > 0
    )


def load_tasks(summary: dict[str, dict[str, float]], partition: str) -> list[dict]:
    """Return one load task per region, ready for `.expand_kwargs()`.

    Args:
        summary: The output of `summarise_by_region`.
        partition: The partition being loaded, e.g. "20260115".

    Returns:
        A list of dicts, each with a `region` and a `partition` key.
    """
    return [
        {"region": region, "partition": partition}
        for region in regions_to_process(summary)
    ]


def region_summary_csv(summary: dict[str, dict[str, float]], region: str) -> str:
    """Render the summary for a single region.

    Args:
        summary: The output of `summarise_by_region`.
        region: The region to render.

    Returns:
        A CSV document with a header and one data row.
    """
    bucket = summary[region]
    return (
        "region,order_count,revenue_eur\n"
        f"{region},{int(bucket['order_count'])},{bucket['revenue_eur']:.2f}\n"
    )
