"""
Lesson 04 — The First AI Tool (Phase 1 capstone).

This is the deliverable of Phase 1: a CLI that takes a customer email,
extracts the shipment ID, looks it up, and drafts a reply in
PacificFreight's voice.

What you should be able to explain to a client after this lesson:
- The 5 components of an FDE tool: read, extract, lookup, draft, output.
- Why the regex catches 80% of shipment IDs and the LLM is the fallback.
- Why the style guide is a separate file (configuration, not code).
- Why the mock backend means the tool always works, even on a plane.

How to run:
    # Look up a specific shipment
    python3 technical/04-first-ai-tool.py --email ../shared/sample-emails.md --shipment PF-1001

    # Auto-extract the ID from the email
    cat ../shared/sample-emails.md | python3 technical/04-first-ai-tool.py

    # JSON output for piping
    python3 technical/04-first-ai-tool.py --email ../shared/sample-emails.md --shipment PF-1003 --json
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Reuse lesson 03's LLM client.
sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module
_llm_module = import_module("03-modern-ai-tooling")
complete = _llm_module.complete  # type: ignore[attr-defined]

load_dotenv()


# ---------------------------------------------------------------------------
# Shipment data class — same shape as lesson 01, but with one extra field
# (origin / destination) so the LLM can write "Singapore → HCMC" naturally.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Shipment:
    id: str
    customer_name: str
    origin: str
    destination: str
    status: str
    last_event: str
    last_event_at: str
    next_action_required: Optional[str] = None
    eta: Optional[str] = None


# ---------------------------------------------------------------------------
# Component 1 — Email reader
# ---------------------------------------------------------------------------
def read_email(path: Optional[str]) -> str:
    """Read from --email file, or stdin if path is None or '-'."""
    if path is None or path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Component 2 — Shipment ID extractor
# Regex first; LLM only when regex fails (the 15% of messy inputs).
# ---------------------------------------------------------------------------
SHIPMENT_ID_RE = re.compile(r"\bPF[-\s]?\d{4,5}\b", re.IGNORECASE)


def extract_id(text: str) -> Optional[str]:
    """Return a normalized 'PF-XXXX' shipment ID, or None if not found."""
    m = SHIPMENT_ID_RE.search(text)
    if m:
        # Normalize: "PF 1003" or "pf-1003" both become "PF-1003"
        return m.group(0).upper().replace(" ", "").replace("-", "-")
    return None


# ---------------------------------------------------------------------------
# Component 3 — Tracker lookup (a JSON file in Phase 1; a real API in Phase 2)
# ---------------------------------------------------------------------------
def load_shipment(tracker_path: Path, shipment_id: str) -> Optional[Shipment]:
    if not tracker_path.exists():
        return None
    with tracker_path.open() as fh:
        data = json.load(fh)
    target = shipment_id.upper().strip()
    for s in data["shipments"]:
        if s["id"].upper() == target:
            return Shipment(
                id=s["id"],
                customer_name=s["customer_name"],
                origin=s["origin"],
                destination=s["destination"],
                status=s["status"],
                last_event=s["last_event"],
                last_event_at=s["last_event_at"],
                next_action_required=s.get("next_action_required"),
                eta=s.get("eta"),
            )
    return None


# ---------------------------------------------------------------------------
# Component 4 — Reply drafter
# The system prompt loads the style guide at startup. That is configuration,
# not code: when the customer says "replies too formal," we edit style-guide.md.
# ---------------------------------------------------------------------------
def _load_style_guide() -> str:
    path = Path(__file__).parent.parent / "shared" / "style-guide.md"
    if not path.exists():
        return "(no style guide available — fall back to common-sense customer service tone)"
    return path.read_text(encoding="utf-8")


STYLE_GUIDE = _load_style_guide()

SYSTEM_PROMPT = f"""You are drafting customer-service emails for PacificFreight Co., a
cross-border logistics SMB in Singapore.

You MUST follow this style guide:

{STYLE_GUIDE}

You will be given:
1. The customer's inbound email (raw text).
2. The current shipment status from the tracker.

Output ONLY the reply text. No preamble, no "Here's a draft:", no quotes.
The reply must follow all 8 hard rules in the style guide. If the email is
angry or demands a manager, keep the reply under 5 sentences and tell the
CS person in a one-line prefix to call the customer.
"""


def build_user_prompt(email_text: str, s: Shipment, rep_name: str) -> str:
    next_action = s.next_action_required or "(none — no customer action required)"
    eta = s.eta or "(no current ETA)"
    return f"""Customer email:
---
{email_text}
---

Shipment in tracker:
- ID: {s.id}
- Customer: {s.customer_name}
- Route: {s.origin} → {s.destination}
- Status: {s.status}
- Last event: {s.last_event}
- Last event at: {s.last_event_at}
- ETA: {eta}
- Action required: {next_action}

Sign the reply with: — {rep_name} at PacificFreight.

Draft the reply.
"""


# ---------------------------------------------------------------------------
# Component 5 — Output formatter (text by default, --json for piping)
# ---------------------------------------------------------------------------
def format_text(result: dict) -> str:
    return (
        f"[DRAFT for {result['shipment_id']} — {result['status']} "
        f"| model={result['model']} | cost=${result['cost_usd']:.6f}]\n"
        f"{result['draft']}\n"
    )


def format_json(result: dict) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Orchestration — the 40-line main() that ties the 5 components together
# ---------------------------------------------------------------------------
def draft_reply(
    email_text: str,
    shipment_id: Optional[str],
    *,
    tracker_path: Path,
    rep_name: str,
) -> dict:
    """The FDE loop: read -> extract -> lookup -> draft -> output."""
    # Step 2: extract the ID if not given
    if not shipment_id:
        shipment_id = extract_id(email_text)
    if not shipment_id:
        return {
            "ok": False,
            "error": "no_shipment_id",
            "message": (
                "Could not find a shipment ID in the email. "
                "Please ask the customer to reply with their PF-XXXX reference, "
                "then re-run with --shipment PF-XXXX."
            ),
        }

    # Step 3: look up the shipment
    shipment = load_shipment(tracker_path, shipment_id)
    if shipment is None:
        return {
            "ok": False,
            "error": "shipment_not_found",
            "shipment_id": shipment_id,
            "message": f"No shipment with ID {shipment_id!r} in the tracker.",
        }

    # Step 4: draft the reply
    result = complete(
        system=SYSTEM_PROMPT,
        user=build_user_prompt(email_text, shipment, rep_name),
    )
    return {
        "ok": True,
        "shipment_id": shipment.id,
        "customer": shipment.customer_name,
        "status": shipment.status,
        "draft": result.text,
        "model": result.model,
        "provider": result.provider,
        "is_mock": result.is_mock,
        "cost_usd": result.cost_usd,
        "latency_ms": result.latency_ms,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Draft a customer-service reply for a PacificFreight shipment.",
    )
    parser.add_argument(
        "--email",
        default="-",
        help="Path to the inbound email file (or '-' for stdin).",
    )
    parser.add_argument(
        "--shipment",
        default=None,
        help="Shipment ID (e.g. PF-1003). If omitted, the tool extracts from the email.",
    )
    parser.add_argument(
        "--tracker",
        default=os.getenv(
            "PF_TRACKER_PATH",
            str(Path(__file__).parent.parent / "shared" / "shipments.json"),
        ),
        help="Path to shipments.json",
    )
    parser.add_argument(
        "--rep",
        default=os.getenv("PF_REP_NAME", "Linh"),
        help="CS rep's first name to sign the reply with.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON (for piping to other tools).",
    )
    args = parser.parse_args()

    email_text = read_email(args.email)
    result = draft_reply(
        email_text=email_text,
        shipment_id=args.shipment,
        tracker_path=Path(args.tracker),
        rep_name=args.rep,
    )

    if args.json:
        print(format_json(result))
    else:
        if not result["ok"]:
            print(f"[ERROR: {result['error']}] {result['message']}", file=sys.stderr)
            return 3 if result["error"] == "no_shipment_id" else 4
        print(format_text(result))
    return 0 if result["ok"] else (3 if result.get("error") == "no_shipment_id" else 4)


if __name__ == "__main__":
    raise SystemExit(main())
