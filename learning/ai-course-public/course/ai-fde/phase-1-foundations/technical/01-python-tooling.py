"""
Lesson 01 — pf-lookup: a tiny CLI that reads shipments.json.

What you should be able to explain to a client after this lesson:
- What a virtual environment is, and why we use one.
- Why we keep secrets in .env, not in source.
- Why we use argparse (so the customer can run the tool themselves).

How to run:
    python3 technical/01-python-tooling.py PF-1003
    python3 technical/01-python-tooling.py --help
    python3 technical/01-python-tooling.py PF-1003 --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads .env into os.environ (does NOT overwrite existing vars)


@dataclass(frozen=True)
class Shipment:
    id: str
    customer_name: str
    status: str
    last_event: str
    last_event_at: str
    next_action_required: str | None = None


def load_shipment(tracker_path: Path, shipment_id: str) -> Shipment | None:
    """Look up a shipment by ID. Returns None if not found."""
    if not tracker_path.exists():
        raise FileNotFoundError(f"tracker not found at {tracker_path}")
    with tracker_path.open() as fh:
        data = json.load(fh)
    target = shipment_id.upper().strip()
    for s in data["shipments"]:
        if s["id"].upper() == target:
            return Shipment(
                id=s["id"],
                customer_name=s["customer_name"],
                status=s["status"],
                last_event=s["last_event"],
                last_event_at=s["last_event_at"],
                next_action_required=s.get("next_action_required"),
            )
    return None


def format_summary(s: Shipment) -> str:
    """Print a one-screen summary a human can read in 5 seconds."""
    lines = [
        f"Shipment {s.id}  (customer: {s.customer_name})",
        f"Status: {s.status}",
        f"Last event ({s.last_event_at}): {s.last_event}",
    ]
    if s.next_action_required:
        lines.append(f"Action: {s.next_action_required}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Look up a PacificFreight shipment by ID.",
    )
    parser.add_argument("shipment_id", help="e.g. PF-1003")
    parser.add_argument(
        "--tracker",
        default=os.getenv(
            "PF_TRACKER_PATH",
            str(Path(__file__).parent.parent / "shared" / "shipments.json"),
        ),
        help="Path to shipments.json",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of formatted text (for piping to other tools)",
    )
    args = parser.parse_args()

    tracker_path = Path(args.tracker)
    try:
        shipment = load_shipment(tracker_path, args.shipment_id)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if shipment is None:
        print(f"ERROR: no shipment with ID {args.shipment_id!r}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(shipment.__dict__, indent=2, ensure_ascii=False))
    else:
        print(format_summary(shipment))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
