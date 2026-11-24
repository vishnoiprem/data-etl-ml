"""Configuration: paths, runtime settings, and the business assumptions.

**Every number this project makes a decision on lives in this file**, and
:func:`assumptions_snapshot` exports them with a provenance tag so a reader can
see exactly which figures are published benchmarks, which are industry
estimates, and which are design choices of this simulation.

That split matters because a TMS is mostly a pile of assumptions wearing a
cost model. If the assumptions are buried inside the simulation code, the
simulation is unfalsifiable: nobody can disagree with a number they cannot
find. So they are all here, in one place, labelled.

Provenance tags
---------------
``published``
    A real, citable figure from an operator, an industry report, or a
    carrier's own published documentation.
``estimated``
    A plausible industry range that is not attributable to a single published
    source. Directionally useful, not authoritative.
``design``
    A choice made by this simulation for tractability or to exercise a code
    path. Not a claim about the real world.

Sub-parts
---------
- Path constants (``PROJECT_ROOT``, ``DATA_DIR``, ``REPORTS_DIR``).
- :class:`Settings` — runtime knobs, read from the environment.
- :class:`ValueConfig` — the business assumptions.
- :func:`assumptions_snapshot` — the auditable export.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

#: Project root — the directory holding README.md, Makefile and app.py.
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

#: Where the checked-in corpus and any generated artefacts live.
DATA_DIR: Path = PROJECT_ROOT / "data"

#: Where the eval harness and the demo write their output. Created on demand.
REPORTS_DIR: Path = PROJECT_ROOT / "reports"


# --------------------------------------------------------------------------- #
# Runtime settings
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime knobs, read from the environment.

    The project is offline by default and every one of these has a working
    default, so a clean checkout runs with no environment set up at all.
    """

    #: Master seed for the corpus generator. Same seed, same world, every run.
    seed: int = field(default=20261121)

    #: Number of simulated operating days in the corpus.
    days: int = field(default=7)

    #: Number of orders generated per day, before the peak-day multiplier.
    orders_per_day: int = field(default=260)

    #: Which simulated day the "now" clock sits on. Fixed, so every metric,
    #: ETA and SLA verdict in this project is reproducible.
    #:
    #: The clock sits at the **end of the operating window** — the day
    #: after the last day of demand — so that every order in the corpus
    #: has come due and the headline KPIs measure the whole network
    #: rather than its first three days.
    #:
    #: This matters more than it looks. A clock parked mid-week measures
    #: the on-time rate of the orders whose promises have passed, and
    #: silently drops the rest — including every order on the campaign
    #: day, which is the hardest day in the corpus and the one whose
    #: behaviour a reviewer is most interested in. The on-time rate then
    #: looks like a property of the calendar rather than of the network.
    now_day_index: int = field(default=7)

    #: Multiplier applied to demand on the designated peak (campaign) day.
    peak_multiplier: float = field(default=3.4)

    #: Minimum days between a failed delivery attempt and the next retry.
    retry_spacing_days: int = field(default=1)

    #: Maximum delivery attempts before the parcel is returned to origin.
    max_attempts: int = field(default=3)

    #: Dimension-weight divisor in cm³/kg. 5000 is the surface-parcel divisor
    #: used by DHL/FedEx and by Indian D2C surface contracts.
    dim_divisor: float = field(default=5000.0)

    #: When true, the simulator stops at the first impossible constraint
    #: instead of degrading gracefully. Used by the tests.
    strict: bool = field(default=False)

    @classmethod
    def defaults(cls) -> dict[str, Any]:
        """The declared default for every field.

        Read from the dataclass fields rather than from the class
        attributes. With ``slots=True`` the class attributes are
        ``member_descriptor`` objects, not the values — so ``cls.seed``
        would return a descriptor instead of the number.
        """

        import dataclasses

        return {
            f.name: f.default
            for f in dataclasses.fields(cls)
            if f.default is not dataclasses.MISSING
        }

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from ``TMS_*`` environment variables.

        Every variable is optional. An unparseable integer falls back to the
        class default rather than raising, because a typo in a shell export
        should not stop the demo from running.
        """

        defaults = cls.defaults()

        def _int(name: str, key: str) -> int:
            raw = os.environ.get(name)
            if raw is None:
                return int(defaults[key])
            try:
                return int(raw)
            except ValueError:
                return int(defaults[key])

        def _float(name: str, key: str) -> float:
            raw = os.environ.get(name)
            if raw is None:
                return float(defaults[key])
            try:
                return float(raw)
            except ValueError:
                return float(defaults[key])

        return cls(
            seed=_int("TMS_SEED", "seed"),
            days=_int("TMS_DAYS", "days"),
            orders_per_day=_int("TMS_ORDERS_PER_DAY", "orders_per_day"),
            now_day_index=_int("TMS_NOW_DAY_INDEX", "now_day_index"),
            peak_multiplier=_float("TMS_PEAK_MULTIPLIER", "peak_multiplier"),
            retry_spacing_days=_int("TMS_RETRY_SPACING_DAYS", "retry_spacing_days"),
            max_attempts=_int("TMS_MAX_ATTEMPTS", "max_attempts"),
            dim_divisor=_float("TMS_DIM_DIVISOR", "dim_divisor"),
            strict=os.environ.get("TMS_STRICT", "").lower() in {"1", "true", "yes"},
        )


# --------------------------------------------------------------------------- #
# Business assumptions
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ValueConfig:
    """Every business assumption the simulation makes.

    Grouped by the kind of decision the number feeds, and each tagged with
    its provenance so it can be argued with. See the module docstring for the
    meaning of the three tags.

    Nothing else in the codebase is allowed to hard-code a business rate.
    If a rate needs to change, it changes here.
    """

    # -- Service levels ---------------------------------------------------- #
    # A service level is a promise made to the customer at checkout. The
    # promise window is generated relative to the order time.
    #
    # The windows have to be physically achievable against the rest of the
    # model, or the whole network is late by construction and the KPI
    # numbers say nothing. A same-day order needs: pick and pack, a courier
    # already on shift, and the drive. That is roughly 4 hours of
    # warehouse work plus an afternoon's delivery window, so a 14-hour
    # promise is what a same-day service can actually carry.
    service_level_hours: dict[str, int] = field(
        default_factory=lambda: {
            "same_day": 14,
            "next_day": 30,
            "economy": 96,
            "express_cross_border": 168,
        }
    )

    #: Share of orders per service level. ``design``, except same_day which
    #: is shaped by the quick-commerce market.
    service_level_mix: dict[str, float] = field(
        default_factory=lambda: {
            "same_day": 0.18,
            "next_day": 0.47,
            "economy": 0.28,
            "express_cross_border": 0.07,
        }
    )

    #: The hour after which the same-day service is no longer offered.
    #:
    #: This is a real operating lever, not a modelling convenience. A
    #: same-day order placed at 15:00 needs the parcel picked, packed,
    #: loaded, driven and signed for inside a same-day window, and no
    #: network can do that reliably. So the checkout stops offering
    #: same-day once the cut-off passes and falls back to next-day.
    #:
    #: Without the cut-off the network reports a catastrophic on-time rate
    #: for a promise it never had any business making — and the interesting
    #: question ("how late, and why") gets buried under the failures that
    #: were guaranteed from the moment the order was placed.
    same_day_cutoff_hour: int = 11

    # -- Payment mix ------------------------------------------------------- #
    #: Share of orders paid cash-on-delivery, by city tier. COD adoption is
    #: published at 55-65% in Indian tier-2/3 and 47-60% across the Middle
    #: East and the Philippines; pre-paid orders carry a 3-5x lower RTO rate.
    cod_share_by_tier: dict[str, float] = field(
        default_factory=lambda: {
            "tier1": 0.38,
            "tier2": 0.58,
            "tier3": 0.64,
        }
    )

    #: RTO (return-to-origin) rate for cash-on-delivery orders, by tier.
    #: Published benchmark: 12-22% tier-1, 18-32% tier-2, 25-40%+ tier-3/4.
    cod_rto_rate_by_tier: dict[str, float] = field(
        default_factory=lambda: {
            "tier1": 0.17,
            "tier2": 0.25,
            "tier3": 0.33,
        }
    )

    #: RTO rate for pre-paid orders. Pre-paid is 3-5x lower than COD.
    prepaid_rto_rate: float = 0.07

    # -- Address quality --------------------------------------------------- #
    #: Share of orders whose address carries at least one quality flag. Address
    #: problems are a top-5 driver of failed delivery in published breakdowns.
    flagged_address_share: float = 0.115

    #: Multiplier on first-attempt failure probability per address-quality
    #: point below perfect. A score of 0.6 gives 1.0 - 0.6 = 0.4x the
    #: baseline failure rate.
    address_quality_failure_multiplier: float = 1.0

    # -- Fleet ------------------------------------------------------------- #
    #: Average observed speed by mode in km/h during urban rush hour.
    #: Published: urban delivery speed in Indian metros runs under 15 km/h.
    mode_speed_kmh: dict[str, float] = field(
        default_factory=lambda: {
            "walk": 5.0,
            "bike": 14.0,
            "three_wheeler": 12.0,
            "van": 16.0,
        }
    )

    #: Carry capacity per courier by mode: (max kg, max m³, max parcels).
    #: Published operating envelopes: bikes 15-25 kg, 3-wheelers 50-100 kg,
    #: vans 400-800 kg / 6-10 m³.
    mode_capacity: dict[str, tuple[float, float, int]] = field(
        default_factory=lambda: {
            "walk": (15.0, 1.2, 30),
            "bike": (25.0, 0.35, 45),
            "three_wheeler": (90.0, 1.8, 80),
            "van": (600.0, 9.0, 140),
        }
    )

    #: Fixed daily cost per active courier by mode, and the per-stop and
    #: per-kilometre variable costs. ``estimated`` — anchored to published
    #: per-parcel rate cards, not quoted from one.
    courier_fixed_cost: dict[str, float] = field(
        default_factory=lambda: {
            "walk": 180.0,
            "bike": 320.0,
            "three_wheeler": 420.0,
            "van": 700.0,
        }
    )

    courier_cost_per_stop: dict[str, float] = field(
        default_factory=lambda: {
            "walk": 14.0,
            "bike": 32.0,
            "three_wheeler": 48.0,
            "van": 85.0,
        }
    )

    courier_cost_per_km: dict[str, float] = field(
        default_factory=lambda: {
            "walk": 0.0,
            "bike": 4.0,
            "three_wheeler": 6.0,
            "van": 11.0,
        }
    )

    #: Minutes spent on site per stop, for service time. Signing adds
    #: materially; multi-order drops amortise it.
    service_minutes_base: float = 3.5
    service_minutes_per_parcel: float = 1.2

    #: Minutes to pick, pack and manifest one order.
    #:
    #: This is the *service time* of a pick-and-pack station, not a
    #: constant lag applied to every order. The warehouse is a bank of
    #: parallel stations working a FIFO queue: they work through the
    #: day's orders in the order they arrive, and each takes this long.
    #:
    #: The distinction matters because a constant lag makes every order
    #: ready the same fixed interval after it was placed, which is only
    #: true when the warehouse is idle. A real fulfilment centre is idle
    #: in the morning and backed up in the evening, and that backlog is
    #: exactly what decides whether the evening wave can carry the
    #: evening's demand.
    pick_pack_minutes: float = 20.0

    #: How many pick-and-pack stations the fulfilment centre runs, and the
    #: hours a day they work.
    #:
    #: The station count is the **baseline**, and the warehouse scales
    #: with the day's demand from it — a real fulfilment centre brings
    #: on temporary pickers for a campaign, and a model that does the same
    #: is honest about the fact that the backlog on a peak day is a
    #: staffing decision rather than a law of nature.
    pick_pack_stations: int = 12

    #: Extra pick-and-pack stations per hundred extra orders on a day.
    #: A fulfilment centre adds people as the day's volume becomes clear;
    #: the same rule here keeps the peak day's backlog a couple of hours
    #: rather than a whole day.
    pick_pack_stations_per_100_orders: float = 4.0

    warehouse_start_hour: float = 6.0
    warehouse_end_hour: float = 23.0

    #: Courier shift length in hours, and the daily dispatch window.
    #:
    #: The shift has to straddle the demand curve. Orders peak in the
    #: evening, so a shift that starts at 6am and ends at 4pm is a shift
    #: that is over before half the day's orders have even been picked —
    #: and a dispatcher that respects the shift boundary will then defer
    #: every evening order to the next day. Real last-mile shifts start
    #: with the morning wave and run deep into the evening.
    shift_hours: float = 12.0
    dispatch_start_hour: float = 7.0
    dispatch_end_hour: float = 23.0

    #: The evening wave. Demand peaks after the evening meal, and a day
    #: shift that ends before the peak cannot serve it. The evening wave
    #: overlaps the day wave, which is what keeps the promise on orders
    #: placed late in the afternoon.
    evening_shift_start_hour: float = 14.0
    evening_shift_hours: float = 9.0

    #: Share of the roster that works the evening wave rather than the day
    #: wave. Demand is evening-weighted, so the evening wave is the larger
    #: of the two.
    evening_shift_share: float = 0.45

    #: Surge courier premium as a multiple of the normal fixed cost.
    surge_premium_multiplier: float = 1.45

    #: Share of surge demand met by hiring surge couriers, versus deferring
    #: to the next day's wave or accepting an SLA breach.
    surge_hiring_share: float = 0.55

    # -- Delivery outcomes ------------------------------------------------- #
    #: Baseline first-attempt failure probability, before address quality,
    #: COD, PIN-code risk and time-of-day adjustments.
    baseline_first_attempt_failure: float = 0.145

    #: Conditional probability of a given failure reason, given a failure.
    failure_reason_mix: dict[str, float] = field(
        default_factory=lambda: {
            "CUSTOMER_UNAVAILABLE": 0.40,
            "ADDRESS_INCORRECT": 0.18,
            "INSUFFICIENT_CASH": 0.14,
            "ADDRESS_UNREACHABLE": 0.09,
            "CUSTOMER_REFUSED": 0.10,
            "PREMIUM_MIXED": 0.05,
            "WEATHER": 0.04,
        }
    )

    #: Probability the customer is available on a retry, conditional on the
    #: first attempt failing for availability reasons. Attempts do recover.
    retry_recovery_rate: float = 0.55

    #: Published COD remittance cycles by carrier, in days after delivery.
    cod_remittance_days: dict[str, int] = field(
        default_factory=lambda: {
            "ninja_van": 2,
            "delhivery": 2,
            "xpressbees": 3,
            "jnt_express": 3,
            "lalamove": 1,
            "aggregator": 5,
        }
    )

    #: Published pre-dispatch SMS confirmation cuts COD RTO by 15-25 points.
    cod_confirm_rto_reduction: float = 0.20

    #: Probability a COD order receives the confirmation SMS. Published
    #: confirmation rates ramp from 55-65% in the first 30 days to 75-85%
    #: once mature.
    cod_confirm_reach_rate: float = 0.62

    # -- SLA --------------------------------------------------------------- #
    #: Published OTD target is 92-95%; stretch 97%+.
    otd_target: float = 0.93

    #: Published first-attempt-delivery target is 78-88%; stretch 90%+.
    fad_target: float = 0.82

    #: Published RTO target is 12-18%; stretch under 10%.
    rto_target: float = 0.18

    #: Published damage/loss rate is 0.3-1.0%.
    damage_rate: float = 0.006

    # -- Fraud ------------------------------------------------------------- #
    #: Base rate of orders the risk model flags. Kept low enough that a
    #: scorer which flags everything is visibly wrong.
    fraud_base_rate: float = 0.045

    #: Risk score at or above which the order is held for confirmation.
    fraud_hold_threshold: float = 0.55

    #: Risk score at or above which the order is blocked outright.
    fraud_block_threshold: float = 0.82

    #: Discount applied to the risk score when the order is pre-paid.
    fraud_prepaid_discount: float = 0.35

    # -- Cost -------------------------------------------------------------- #
    #: Cost of a failed delivery attempt (the extra stop, the extra day).
    failed_attempt_cost: float = 28.0

    #: Cost of returning a parcel to origin, as a multiple of forward freight.
    rto_cost_multiplier: float = 1.8

    #: Courier-side fraud: POD recorded further than this from the planned
    #: stop is treated as an off-route POD.
    pod_geofence_meters: float = 250.0

    # -- Parcel weights ---------------------------------------------------- #
    #: Parcel actual-weight log-normal parameters (kg).
    weight_mu: float = 0.35
    weight_sigma: float = 0.62

    #: Parcel dimension log-normal parameters (cm).
    dim_mu: float = 2.85
    dim_sigma: float = 0.42

    #: Share of orders shipped as more than one parcel.
    multi_package_share: float = 0.032

    #: Order value in currency units, log-normal.
    order_value_mu: float = 5.4
    order_value_sigma: float = 0.85


#: The single shared configuration used by the whole project.
DEFAULT_VALUES = ValueConfig()


@dataclass(frozen=True, slots=True)
class Assumptions:
    """A labelled assumption, exported for the audit trail."""

    key: str
    value: Any
    provenance: str
    note: str


def assumptions_snapshot(values: ValueConfig | None = None) -> list[Assumptions]:
    """Export every business assumption with its provenance tag.

    The tags are curated rather than derived, because the distinction between
    "published benchmark" and "industry estimate" is a judgement call about
    the number, not something a reflection can work out.
    """

    cfg = values or DEFAULT_VALUES
    raw = asdict(cfg)

    published = {
        "cod_share_by_tier",
        "cod_rto_rate_by_tier",
        "prepaid_rto_rate",
        "mode_speed_kmh",
        "mode_capacity",
        "service_minutes_base",
        "cod_remittance_days",
        "cod_confirm_rto_reduction",
        "otd_target",
        "fad_target",
        "rto_target",
        "damage_rate",
        "failed_attempt_cost",
        "dim_divisor",
    }

    estimated = {
        "cod_confirm_reach_rate",
        "courier_fixed_cost",
        "courier_cost_per_stop",
        "courier_cost_per_km",
        "baseline_first_attempt_failure",
        "retry_recovery_rate",
        "address_quality_failure_multiplier",
        "failure_reason_mix",
        "rto_cost_multiplier",
    }

    notes = {
        "cod_share_by_tier": "Published: COD is 55-65% of orders in Indian tier-2/3, "
        "47-60% across the Middle East and the Philippines.",
        "cod_rto_rate_by_tier": "Published: 12-22% tier-1, 18-32% tier-2, 25-40%+ tier-3/4.",
        "prepaid_rto_rate": "Published: pre-paid orders carry a 3-5x lower RTO rate than COD.",
        "mode_speed_kmh": "Published: urban delivery speed in Indian metros runs under 15 km/h "
        "during rush hour.",
        "mode_capacity": "Published operating envelopes for bikes, 3-wheelers and vans.",
        "cod_remittance_days": "Published carrier cycles: T+1 (Lalamove) to T+5 (aggregators).",
        "cod_confirm_rto_reduction": "Published: pre-dispatch confirmation SMS cuts COD RTO by "
        "15-25 percentage points.",
        "otd_target": "Published benchmark range 92-95%, stretch 97%+.",
        "fad_target": "Published benchmark range 78-88%, stretch 90%+.",
        "rto_target": "Published benchmark range 12-18%.",
        "damage_rate": "Published benchmark range 0.3-1.0%.",
        "failed_attempt_cost": "Estimated from the published forward/reverse freight spread.",
        "service_minutes_base": "Estimated: signature capture adds materially to on-site time.",
        "dim_divisor": "Published: 5000 cm3/kg surface divisor (DHL, FedEx, Indian D2C surface).",
    }

    out: list[Assumptions] = []
    for key, value in raw.items():
        if key in published:
            tag = "published"
        elif key in estimated:
            tag = "estimated"
        else:
            tag = "design"
        out.append(
            Assumptions(
                key=key,
                value=value,
                provenance=tag,
                note=notes.get(key, ""),
            )
        )
    return out


def ensure_dirs() -> None:
    """Create the runtime directories if they do not exist yet."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
