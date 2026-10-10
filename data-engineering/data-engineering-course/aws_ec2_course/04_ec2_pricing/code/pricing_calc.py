"""EC2 pricing calculator (stdlib only).

Illustrative 2026 us-east-1 Linux on-demand rates for five instance types,
plus discount models for Reserved Instances, Savings Plans, and Spot.

This module is deliberately offline. It does NOT call the AWS Pricing API.
See ``code/README.md`` for instructions on extending it.

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

from __future__ import annotations

from typing import Optional

# Illustrative 2026 us-east-1 Linux on-demand USD/hour rates.
# Numbers are rounded and not meant for production billing.
PRICING = {
    "t3.micro":   0.0104,
    "t3.small":   0.0208,
    "m5.large":   0.0960,
    "c5.xlarge":  0.1920,
    "r5.large":   0.1260,
}

# Discount factors applied to on-demand. Values < 1.0.
DISCOUNTS = {
    "reserved_1y_no_upfront":      0.60,   # ~40% off
    "reserved_1y_partial_upfront": 0.50,   # ~50% off
    "reserved_1y_all_upfront":     0.46,   # ~54% off
    "reserved_3y_no_upfront":      0.50,   # ~50% off
    "reserved_3y_partial_upfront": 0.42,   # ~58% off
    "reserved_3y_all_upfront":     0.40,   # ~60% off
    "savings_plan_compute_1y":     0.80,   # ~20% off
    "savings_plan_compute_3y":     0.73,   # ~27% off
    "savings_plan_ec2_1y":        0.73,   # ~27% off
    "savings_plan_ec2_3y":         0.63,   # ~37% off
}

VALID_PAYMENTS = {"no_upfront", "partial_upfront", "all_upfront"}


def _on_demand_rate(instance_type: str) -> float:
    """Return the on-demand hourly rate for ``instance_type``.

    Raises ``KeyError`` (via the dict lookup) if the type is unknown.
    """
    return PRICING[instance_type]


def on_demand(instance_type: str, hours: float) -> float:
    """Cost under on-demand pricing. Straight multiply."""
    if hours < 0:
        raise ValueError("hours must be non-negative")
    return _on_demand_rate(instance_type) * hours


def reserved(
    instance_type: str,
    hours: float,
    term_years: int = 1,
    payment: str = "no_upfront",
) -> float:
    """Cost under Reserved Instance pricing.

    Discount depends on the term length and the upfront payment option.
    Defaults are 1-year term with no upfront (~40% off).
    """
    if hours < 0:
        raise ValueError("hours must be non-negative")
    if term_years not in (1, 3):
        raise ValueError("term_years must be 1 or 3")
    if payment not in VALID_PAYMENTS:
        raise ValueError(f"payment must be one of {sorted(VALID_PAYMENTS)}")
    key = f"reserved_{term_years}y_{payment}"
    return _on_demand_rate(instance_type) * hours * DISCOUNTS[key]


def savings_plan(
    instance_type: str,
    hours: float,
    plan_type: str = "compute",
    term_years: int = 3,
) -> float:
    """Cost under Savings Plans pricing.

    Defaults to a 3-year Compute Savings Plan (~27% off).
    """
    if hours < 0:
        raise ValueError("hours must be non-negative")
    if plan_type not in ("compute", "ec2"):
        raise ValueError("plan_type must be 'compute' or 'ec2'")
    if term_years not in (1, 3):
        raise ValueError("term_years must be 1 or 3")
    plan_short = "compute" if plan_type == "compute" else "ec2"
    key = f"savings_plan_{plan_short}_{term_years}y"
    return _on_demand_rate(instance_type) * hours * DISCOUNTS[key]


def spot(
    instance_type: str,
    hours: float,
    spot_price: Optional[float] = None,
) -> float:
    """Cost under Spot pricing.

    If ``spot_price`` is not given, defaults to 30% of on-demand, which is
    in the right ballpark for many stable Linux types in us-east-1.
    """
    if hours < 0:
        raise ValueError("hours must be non-negative")
    if spot_price is None:
        spot_price = _on_demand_rate(instance_type) * 0.30
    if spot_price < 0:
        raise ValueError("spot_price must be non-negative")
    return spot_price * hours


def estimate_monthly(
    instance_type: str,
    hours_per_month: float = 730,
    model: str = "on_demand",
    term_years: int = 3,
    payment: str = "no_upfront",
    plan_type: str = "compute",
    spot_price: Optional[float] = None,
) -> float:
    """Convenience wrapper. Dispatches to the right pricing function."""
    if model == "on_demand":
        return on_demand(instance_type, hours_per_month)
    if model == "reserved":
        return reserved(instance_type, hours_per_month, term_years, payment)
    if model == "savings_plan":
        return savings_plan(instance_type, hours_per_month, plan_type, term_years)
    if model == "spot":
        return spot(instance_type, hours_per_month, spot_price)
    raise ValueError(
        f"unknown model {model!r}; expected one of "
        "'on_demand', 'reserved', 'savings_plan', 'spot'"
    )


def _format(instance_type: str, model: str, cost: float) -> str:
    return f"{instance_type:>10}  {model:<22}  ${cost:>8.2f}"


def main() -> None:
    """Print a side-by-side comparison for one instance type at 730h/month."""
    instance_type = "t3.micro"
    hours = 730.0

    od = on_demand(instance_type, hours)
    print(f"EC2 pricing comparison for {instance_type} @ {hours:.0f}h/month")
    print("-" * 56)
    print(_format(instance_type, "on_demand",                   od))
    print(_format(instance_type, "reserved 1y no-up",          reserved(instance_type, hours, 1, "no_upfront")))
    print(_format(instance_type, "reserved 3y all-up",         reserved(instance_type, hours, 3, "all_upfront")))
    print(_format(instance_type, "savings plan compute 3y",    savings_plan(instance_type, hours, "compute", 3)))
    print(_format(instance_type, "savings plan ec2 3y",        savings_plan(instance_type, hours, "ec2", 3)))
    print(_format(instance_type, "spot (default)",              spot(instance_type, hours)))


if __name__ == "__main__":
    main()
