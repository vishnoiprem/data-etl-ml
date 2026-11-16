"""Supplier quote parsing and validation.

A quote is what a supplier actually offers: an FOB price at a volume, a lead
time, a minimum order quantity, payment terms. This module turns the messy
inbound form of that into a validated :class:`Quote`, and refuses quotes that
cannot be priced.

Validation is deliberately strict. A quote that cannot be validated must not
reach the margin model, because a bad price silently becomes a bad
recommendation.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import QUOTES_PATH

#: A quote above this FOB price is almost certainly a units mistake (someone
#: quoted RMB, or quoted per 100 units). We reject rather than guess.
MAX_PLAUSIBLE_FOB_USD = 500.0

#: Lead times beyond this are not plausible for a consumer-electronics
#: accessory from Shenzhen.
MAX_PLAUSIBLE_LEAD_TIME_DAYS = 180

_CURRENCY_RE = re.compile(r"(?:US\$|\$|USD)\s*([\d,]+(?:\.\d+)?)", re.IGNORECASE)
_CURRENCY_SUFFIX_RE = re.compile(
    r"([\d,]+(?:\.\d+)?)\s*(?:US\$|\$|USD)\b", re.IGNORECASE
)


class QuoteError(ValueError):
    """Raised when a quote cannot be parsed or fails validation."""


@dataclass
class Quote:
    """A validated supplier quote."""

    quote_id: str
    alibaba_id: str
    supplier_name: str
    product: str
    dest_country: str
    order_units: int
    fob_usd: float
    lead_time_days: int
    moq: int
    payment_terms: str = ""
    sample_policy: str = ""
    received_at: str = ""
    notes: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "quote_id": self.quote_id,
            "alibaba_id": self.alibaba_id,
            "supplier_name": self.supplier_name,
            "product": self.product,
            "dest_country": self.dest_country,
            "order_units": self.order_units,
            "fob_usd": self.fob_usd,
            "lead_time_days": self.lead_time_days,
            "moq": self.moq,
            "payment_terms": self.payment_terms,
            "sample_policy": self.sample_policy,
            "received_at": self.received_at,
            "notes": self.notes,
        }


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #


def _default_lead_time_days(alibaba_id: str) -> int | None:
    """The supplier's known lead time, from the verified supplier pool.

    A quote that omits the lead time is not necessarily broken — a supplier
    with a well-known production time can be assumed to quote at it. A
    supplier we know nothing about still has to state one.
    """
    try:
        from .corpus import trade_finder_modules

        vs = trade_finder_modules()["verify_suppliers"]
    except (ImportError, FileNotFoundError):
        return None
    for raw in vs.SUPPLIERS:
        if raw["alibaba_id"] == alibaba_id:
            return int(raw["lead_time_days"])
    return None


def parse_fob_price(value: Any) -> float:
    """Extract a USD FOB price from a number or a free-text string.

    Handles ``"$8.50"``, ``"USD 8.5"``, ``"8.50"`` and ``"8.50 USD"``.
    """
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        raise QuoteError(f"Cannot read a price from {value!r}")
    text = value.strip()
    match = _CURRENCY_RE.search(text)
    if match:
        return float(match.group(1).replace(",", ""))
    # Currency after the number, e.g. "8.50 USD".
    match = _CURRENCY_SUFFIX_RE.search(text)
    if match:
        return float(match.group(1).replace(",", ""))
    # No currency marker: accept a bare number only.
    try:
        return float(text.replace(",", ""))
    except ValueError as exc:
        raise QuoteError(f"Cannot read a price from {value!r}") from exc


def parse_quote(payload: dict[str, Any]) -> Quote:
    """Build a :class:`Quote` from a raw mapping, validating every field."""
    if not isinstance(payload, dict):
        raise QuoteError("A quote payload must be a mapping")

    # Note: `is None` rather than a truthiness check. A quoted price of 0 is
    # present-but-invalid and must be reported as such, not as "missing".
    missing = [
        field_name
        for field_name in ("alibaba_id", "product", "fob_usd", "order_units")
        if payload.get(field_name) is None
    ]
    if missing:
        raise QuoteError(f"Quote is missing required field(s): {', '.join(missing)}")

    if not str(payload["alibaba_id"]).strip():
        raise QuoteError("Quote is missing required field(s): alibaba_id")
    if not str(payload["product"]).strip():
        raise QuoteError("Quote is missing required field(s): product")

    order_units = int(payload["order_units"])
    if order_units <= 0:
        raise QuoteError(f"order_units must be positive, got {order_units}")

    fob_usd = parse_fob_price(payload["fob_usd"])
    if fob_usd <= 0:
        raise QuoteError(f"fob_usd must be positive, got {fob_usd}")
    if fob_usd > MAX_PLAUSIBLE_FOB_USD:
        raise QuoteError(
            f"fob_usd {fob_usd} is above the plausible ceiling of "
            f"${MAX_PLAUSIBLE_FOB_USD}. Check the units before pricing this."
        )

    raw_lead_time = payload.get("lead_time_days")
    if raw_lead_time is None:
        # Fall back to the supplier's known lead time from the verified pool.
        lead_time_days = _default_lead_time_days(str(payload["alibaba_id"]))
        if lead_time_days is None:
            raise QuoteError(
                "Quote is missing required field(s): lead_time_days "
                "(no baseline is known for this supplier)"
            )
    else:
        lead_time_days = int(raw_lead_time)
    if lead_time_days <= 0:
        raise QuoteError(f"lead_time_days must be positive, got {lead_time_days}")
    if lead_time_days > MAX_PLAUSIBLE_LEAD_TIME_DAYS:
        raise QuoteError(
            f"lead_time_days {lead_time_days} exceeds the plausible maximum of "
            f"{MAX_PLAUSIBLE_LEAD_TIME_DAYS} days"
        )

    raw_moq = payload.get("moq")
    moq = order_units if raw_moq is None else int(raw_moq)
    if moq <= 0:
        raise QuoteError(f"moq must be positive, got {moq}")

    return Quote(
        quote_id=str(payload.get("quote_id", f"quote-{payload['alibaba_id']}")),
        alibaba_id=str(payload["alibaba_id"]),
        supplier_name=str(payload.get("supplier_name", payload["alibaba_id"])),
        product=str(payload["product"]),
        dest_country=str(payload.get("dest_country", "IN")),
        order_units=order_units,
        fob_usd=fob_usd,
        lead_time_days=lead_time_days,
        moq=moq,
        payment_terms=str(payload.get("payment_terms", "")),
        sample_policy=str(payload.get("sample_policy", "")),
        received_at=str(payload.get("received_at", "")),
        notes=str(payload.get("notes", "")),
        raw=dict(payload),
    )


def parse_quotes(payloads: list[dict[str, Any]]) -> list[Quote]:
    """Parse many quotes, collecting errors instead of failing on the first.

    A single malformed quote should not stop the agent from pricing the other
    two, but the caller does need to know which one failed and why.
    """
    quotes: list[Quote] = []
    errors: list[str] = []
    for payload in payloads:
        try:
            quotes.append(parse_quote(payload))
        except QuoteError as exc:
            identifier = payload.get("quote_id") or payload.get("alibaba_id") or "<unknown>"
            errors.append(f"{identifier}: {exc}")
    if errors:
        raise QuoteError("; ".join(errors))
    return quotes


def load_quotes(path: Path | None = None) -> list[Quote]:
    """Load the bundled quote fixtures."""
    target = path or QUOTES_PATH
    if not target.exists():
        raise QuoteError(f"Quote file not found: {target}")
    payload = json.loads(target.read_text(encoding="utf-8"))
    return parse_quotes(payload["quotes"])
