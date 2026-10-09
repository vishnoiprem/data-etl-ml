"""Generate the deterministic ``sample_data/`` fixtures.

Run once to populate the directory, or re-run any time you change
the generators in :mod:`common.data_gen`. Every fixture is keyed
on ``seed=42`` so the output is byte-stable across machines.

Usage::

    cd data-engineering-course
    python3 sample_data/generate.py
"""

from __future__ import annotations

import os
import random
import sys
from pathlib import Path

# Make the ``common`` package importable when run from anywhere.
HERE = Path(__file__).resolve().parent
COURSE_ROOT = HERE.parent
sys.path.insert(0, str(COURSE_ROOT))

from common.data_gen import (  # noqa: E402
    make_events,
    make_orders,
    make_products,
    make_users,
    seed_all,
)
from common.csv_utils import write_csv, write_jsonl  # noqa: E402

SEED = 42


def _ensure_dir() -> Path:
    out = HERE
    out.mkdir(parents=True, exist_ok=True)
    return out


def _flatten_order_items(orders, products, seed=SEED):
    """Build ``order_items`` rows by exploding orders into line items."""
    rng = random.Random(seed)
    product_by_id = {p["id"]: p for p in products}
    items = []
    item_id = 1
    for o in orders:
        # Some orders have 1 line item, some have 2-3.
        n_lines = rng.randint(1, 3)
        for _ in range(n_lines):
            pid = rng.choice(list(product_by_id.keys()))
            qty = rng.randint(1, 4)
            unit = product_by_id[pid]["price"]
            items.append({
                "item_id": item_id,
                "order_id": o["order_id"],
                "product_id": pid,
                "quantity": qty,
                "unit_price": unit,
                "line_total": round(qty * unit, 2),
            })
            item_id += 1
    return items


def _make_page_views(users, n=30_000, seed=SEED):
    rng = random.Random(seed)
    pages = [
        "/", "/home", "/products", "/products/{id}", "/cart",
        "/checkout", "/account", "/about", "/contact", "/blog",
    ]
    base_year = 2024
    out = []
    for i in range(n):
        u = rng.choice(users)
        page = rng.choice(pages).replace("{id}", str(rng.randint(1, 50)))
        # Build an ISO timestamp.
        day = rng.randint(1, 365)
        hour = rng.randint(0, 23)
        minute = rng.randint(0, 59)
        ts = f"{base_year}-{(day // 30) + 1:02d}-{(day % 30) + 1:02d}T{hour:02d}:{minute:02d}:00Z"
        out.append({
            "view_id": i + 1,
            "user_id": u["id"],
            "page": page,
            "ts": ts,
            "duration_ms": rng.randint(50, 60_000),
        })
    return out


def _make_transactions(users, n=5_000, seed=SEED):
    rng = random.Random(seed)
    currencies = ["USD", "EUR", "GBP", "JPY", "INR", "BRL"]
    statuses = ["completed", "pending", "failed", "refunded"]
    out = []
    for i in range(1, n + 1):
        u = rng.choice(users)
        day = rng.randint(1, 365)
        ts = f"2024-{(day // 30) + 1:02d}-{(day % 30) + 1:02d}T{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:00Z"
        out.append({
            "txn_id": i,
            "user_id": u["id"],
            "amount": round(rng.uniform(1.0, 1500.0), 2),
            "currency": rng.choice(currencies),
            "ts": ts,
            "status": rng.choice(statuses),
        })
    return out


def _make_support_tickets(users, n=500, seed=SEED):
    rng = random.Random(seed)
    subjects = [
        "Order not received", "Refund request", "Wrong item",
        "Login issue", "Password reset", "Account locked",
        "Billing question", "Promo code not working", "App crash",
        "Feature request",
    ]
    bodies = [
        "Hi, I have an issue with my recent order. Can you help?",
        "The package never arrived. Tracking shows delivered but it's not here.",
        "I'd like to return an item I bought last week.",
        "I can't log in. It says my password is wrong.",
        "Please reset my password.",
        "My account is locked. What do I do?",
        "I was charged twice for the same order.",
        "The promo code SAVE10 isn't working at checkout.",
        "The mobile app crashes when I open the cart.",
        "It would be great if you added dark mode.",
    ]
    statuses = ["open", "pending", "resolved", "closed"]
    out = []
    for i in range(1, n + 1):
        u = rng.choice(users)
        day = rng.randint(1, 365)
        ts = f"2024-{(day // 30) + 1:02d}-{(day % 30) + 1:02d}T{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:00Z"
        subj_idx = rng.randint(0, len(subjects) - 1)
        out.append({
            "ticket_id": i,
            "user_id": u["id"],
            "subject": subjects[subj_idx],
            "body": bodies[subj_idx],
            "created_at": ts,
            "status": rng.choice(statuses),
        })
    return out


def main() -> int:
    _ensure_dir()
    seed_all(SEED)

    print("Generating users (n=200)...")
    users = make_users(n=200, seed=SEED)
    write_csv(HERE / "users.csv", users)

    print("Generating products (n=50)...")
    products = make_products(n=50, seed=SEED)
    write_csv(HERE / "products.csv", products)

    print("Generating orders (n=2000)...")
    # Use a subset of the 200 users for orders, and 50 products.
    order_users = make_users(n=200, seed=SEED)
    products = make_products(n=50, seed=SEED)
    orders = make_orders(n=2000, users=order_users, products=products, seed=SEED)
    # Strip product_id from orders to match the requested schema
    # (order_id, user_id, order_date, total, status).
    order_rows = [
        {
            "order_id": o["order_id"],
            "user_id": o["user_id"],
            "order_date": o["order_date"],
            "total": o["total"],
            "status": o["status"],
        }
        for o in orders
    ]
    write_csv(HERE / "orders.csv", order_rows)

    print("Generating order_items (n~5000)...")
    order_items = _flatten_order_items(orders, products, seed=SEED)
    write_csv(HERE / "order_items.csv", order_items)

    print("Generating events (n=10000)...")
    events = make_events(n=10_000, users=users, seed=SEED)
    write_jsonl(HERE / "events.jsonl", events)

    print("Generating page_views (n=30000)...")
    page_views = _make_page_views(users, n=30_000, seed=SEED)
    write_csv(HERE / "page_views.csv", page_views)

    print("Generating transactions (n=5000)...")
    txns = _make_transactions(users, n=5_000, seed=SEED)
    write_csv(HERE / "transactions.csv", txns)

    print("Generating support_tickets (n=500)...")
    tickets = _make_support_tickets(users, n=500, seed=SEED)
    write_jsonl(HERE / "support_tickets.jsonl", tickets)

    print("Done.")
    print(f"Files in {HERE}:")
    for p in sorted(HERE.iterdir()):
        if p.is_file():
            print(f"  {p.name}  ({p.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
