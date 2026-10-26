"""Deterministic synthetic data generators.

These are the data engineering equivalent of the system design track's
``KeyValueStore`` — a tiny, dependency-free source of realistic-ish
shaped data so exercises can focus on the *transformation* rather
than the *fixture*. Every generator seeds its own ``random.Random``
instance so test snapshots stay stable.

All timestamps are emitted in ISO 8601 (UTC) so the same fixture can
feed SQL, pandas, or a JSON pipeline without conversion.
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

# ---- deterministic seeding helpers -------------------------------------

_DEFAULT_SEED = 42
_FIRST_NAMES = [
    "Alice", "Bob", "Carol", "Dan", "Eve", "Frank", "Grace", "Hank",
    "Ivy", "Judy", "Kara", "Leo", "Mia", "Nate", "Olive", "Paul",
    "Quinn", "Rita", "Sam", "Tara", "Uma", "Vince", "Wendy", "Xander",
    "Yara", "Zane",
]
_LAST_NAMES = [
    "Smith", "Jones", "Patel", "Garcia", "Kim", "Müller", "Nguyen",
    "Brown", "Davis", "Cohen", "Rossi", "Yamada", "Khan", "Lopez",
    "Chen", "Schmidt", "O'Brien", "Hassan", "Ivanov", "Singh",
]
_COUNTRIES = ["US", "UK", "DE", "FR", "IN", "JP", "BR", "CA", "AU", "MX"]
_CATEGORIES = [
    "books", "electronics", "clothing", "home", "toys",
    "grocery", "sports", "beauty", "garden", "automotive",
]
_EVENT_TYPES = [
    "page_view", "click", "add_to_cart", "checkout",
    "signup", "login", "logout", "search", "purchase", "refund",
]
_ORDER_STATUSES = ["pending", "paid", "shipped", "delivered", "cancelled", "refunded"]


def _seeded_random(seed: Optional[int]) -> random.Random:
    """Build a fresh ``random.Random`` from an explicit seed."""
    return random.Random(seed if seed is not None else _DEFAULT_SEED)


def seed_all(seed: int = _DEFAULT_SEED) -> None:
    """Seed both the global ``random`` and the ``hashlib`` SHA1 prefix.

    The hashlib seeding is mostly cosmetic — it just makes any
    hashlib-based pseudo-determinism in downstream code stable.
    """
    random.seed(seed)
    # ``hashlib`` doesn't expose a seed knob on CPython, but the
    # documented call is harmless and documents intent.
    try:
        hashlib.openssl_md5  # type: ignore[attr-defined]
    except AttributeError:
        pass


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso_date(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


# ---- generators ---------------------------------------------------------


def make_users(n: int = 100, seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """Return ``n`` synthetic users.

    Returns a list of dicts with keys: ``id``, ``name``, ``email``,
    ``signup_date`` (ISO date), ``country``.
    """
    rng = _seeded_random(seed)
    base = datetime(2022, 1, 1, tzinfo=timezone.utc)
    users: List[Dict[str, Any]] = []
    for i in range(1, n + 1):
        first = rng.choice(_FIRST_NAMES)
        last = rng.choice(_LAST_NAMES)
        name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower().replace(chr(39), '')}{i}@example.com"
        # Spread signups over ~3 years.
        days_offset = rng.randint(0, 365 * 3)
        signup = base + timedelta(days=days_offset)
        users.append({
            "id": i,
            "name": name,
            "email": email,
            "signup_date": _iso_date(signup),
            "country": rng.choice(_COUNTRIES),
        })
    return users


def make_products(
    n: int = 50, seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Return ``n`` synthetic products.

    Keys: ``id``, ``name``, ``category``, ``price`` (float), ``in_stock`` (bool).
    """
    rng = _seeded_random(seed)
    products: List[Dict[str, Any]] = []
    for i in range(1, n + 1):
        category = rng.choice(_CATEGORIES)
        adjective = rng.choice(["Premium", "Basic", "Deluxe", "Eco", "Smart",
                                 "Classic", "Pro", "Ultra", "Mini", "Max"])
        noun = rng.choice(["Widget", "Gadget", "Thingamajig", "Doohickey",
                            "Contraption", "Device", "Kit", "Set", "Bundle", "Pack"])
        products.append({
            "id": i,
            "name": f"{adjective} {category.rstrip('s').capitalize()} {noun}",
            "category": category,
            "price": round(rng.uniform(1.99, 499.99), 2),
            "in_stock": rng.random() > 0.1,
        })
    return products


def make_orders(
    n: int = 1000,
    users: Optional[List[Dict[str, Any]]] = None,
    products: Optional[List[Dict[str, Any]]] = None,
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Return ``n`` synthetic orders.

    Each order carries a single product for simplicity. ``users`` and
    ``products`` default to freshly generated fixtures so callers
    don't have to wire them up just to demo a join.
    """
    rng = _seeded_random(seed)
    users = users if users is not None else make_users(100, seed=seed)
    products = products if products is not None else make_products(50, seed=seed)
    base = datetime(2023, 1, 1, tzinfo=timezone.utc)
    orders: List[Dict[str, Any]] = []
    for i in range(1, n + 1):
        u = rng.choice(users)
        p = rng.choice(products)
        days_offset = rng.randint(0, 365 * 2)
        ts = base + timedelta(days=days_offset, hours=rng.randint(0, 23))
        orders.append({
            "order_id": i,
            "user_id": u["id"],
            "product_id": p["id"],
            "quantity": rng.randint(1, 5),
            "total": round(p["price"] * rng.randint(1, 5), 2),
            "order_date": _iso(ts),
            "status": rng.choice(_ORDER_STATUSES),
        })
    return orders


def make_events(
    n: int = 10_000,
    users: Optional[List[Dict[str, Any]]] = None,
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Return ``n`` synthetic event records.

    Keys: ``event_id``, ``user_id``, ``event_type``, ``ts`` (ISO 8601),
    ``properties`` (a JSON-ish string so it round-trips through CSV).
    """
    rng = _seeded_random(seed)
    users = users if users is not None else make_users(100, seed=seed)
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    events: List[Dict[str, Any]] = []
    for i in range(1, n + 1):
        u = rng.choice(users)
        et = rng.choice(_EVENT_TYPES)
        seconds_offset = rng.randint(0, 60 * 60 * 24 * 90)
        ts = base + timedelta(seconds=seconds_offset)
        # Properties encoded as a small JSON string to keep the schema flat.
        properties = (
            f'{{"page":"/{rng.choice(["home","product","cart","checkout","account"])}",'
            f'"device":"{rng.choice(["ios","android","web"])}"}}'
        )
        events.append({
            "event_id": i,
            "user_id": u["id"],
            "event_type": et,
            "ts": _iso(ts),
            "properties": properties,
        })
    return events
