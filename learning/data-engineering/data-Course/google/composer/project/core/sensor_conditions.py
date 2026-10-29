"""Pure readiness conditions for the course's sensors.

Sensors are orchestration. The *condition* they evaluate is logic, and
logic belongs here, where it can be unit-tested with no Airflow, no
worker, and no timeout.
"""
from __future__ import annotations

from pipeline_logic import transform_orders


def source_is_ready(
    lines: list[str],
    *,
    expected_rows: int = 0,
    reject_threshold: int = 0,
) -> bool:
    """Return True when the source data is complete enough to proceed.

    This is the condition a `PythonSensor` would evaluate. Keeping it
    pure means the "is the data ready?" rule is tested directly, rather
    than being rediscovered every time the sensor times out at 03:00.

    Args:
        lines: The raw source lines.
        expected_rows: The minimum number of accepted rows required.
        reject_threshold: The maximum number of rejected rows tolerated.

    Returns:
        True when the data is ready to process.
    """
    accepted, rejected = transform_orders(lines)
    if len(accepted) < expected_rows:
        return False
    if len(rejected) > reject_threshold:
        return False
    return True
