"""Tests for pricing_calc.py.

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

from __future__ import annotations

import pytest

from pricing_calc import (
    estimate_monthly,
    on_demand,
    reserved,
    savings_plan,
    spot,
)


def test_on_demand_multiplies():
    """730h at $0.0104/h should be $7.592."""
    cost = on_demand("t3.micro", 730)
    assert cost == pytest.approx(7.592, rel=1e-3)


def test_reserved_cheaper_than_on_demand():
    """A reserved instance at the same hours must be cheaper than on-demand."""
    hours = 730
    inst = "m5.large"
    assert reserved(inst, hours, 1, "no_upfront") < on_demand(inst, hours)
    assert reserved(inst, hours, 3, "all_upfront") < on_demand(inst, hours)


def test_savings_plan_cheaper_than_on_demand():
    """A savings plan at the same hours must be cheaper than on-demand."""
    hours = 730
    inst = "m5.large"
    assert savings_plan(inst, hours, "compute", 3) < on_demand(inst, hours)
    assert savings_plan(inst, hours, "ec2", 3) < on_demand(inst, hours)


def test_spot_uses_overridden_price():
    """If we pass a spot price, the calculator must use it directly."""
    hours = 100
    inst = "t3.small"
    override = 0.05
    expected = override * hours
    assert spot(inst, hours, spot_price=override) == pytest.approx(expected, rel=1e-9)


def test_estimate_monthly_default():
    """estimate_monthly at 730h on the default model equals on-demand at 730h."""
    inst = "t3.micro"
    assert estimate_monthly(inst) == pytest.approx(on_demand(inst, 730), rel=1e-9)


def test_unknown_instance_raises():
    """An unknown instance type must raise (KeyError from the PRICING lookup)."""
    with pytest.raises(KeyError):
        on_demand("zzz.nope", 1)
    with pytest.raises(KeyError):
        estimate_monthly("zzz.nope")
