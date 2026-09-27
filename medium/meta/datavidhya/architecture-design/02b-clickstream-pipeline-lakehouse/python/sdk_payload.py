"""
Canonical clickstream event schema — what SDKs send to the collector.

Design rules:
- All fields optional except event_id, user_id, event_ts, event_name
- PII never leaves the device (user_id hashed at SDK)
- 'properties' is the extensibility hatch for new event types
- 'context' carries A/B experiment tags and campaign info
"""

from __future__ import annotations

import argparse
import json
import random
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional


REQUIRED_FIELDS = {"event_id", "user_id", "event_ts", "event_name"}
KNOWN_EVENT_NAMES = {
    "page_view", "click", "scroll", "form_submit", "purchase",
    "signup", "login", "logout", "share", "comment", "like", "search",
}


@dataclass
class ClickstreamEvent:
    event_id:    str
    user_id:     str
    event_ts:    str           # ISO-8601 UTC
    event_name:  str
    session_id:  Optional[str] = None
    platform:    Optional[str] = None    # 'web' | 'ios' | 'android' | 'server'
    app_version: Optional[str] = None
    country:     Optional[str] = None
    device_class: Optional[str] = None
    user_agent:  Optional[str] = None
    properties:  Dict[str, str] = field(default_factory=dict)
    context:     Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None and v != {} and v != ""}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"))

    def validate(self) -> List[str]:
        """Return list of validation errors (empty list == valid)."""
        errors = []
        for f in REQUIRED_FIELDS:
            if not getattr(self, f, None):
                errors.append(f"missing_required:{f}")
        try:
            datetime.fromisoformat(self.event_ts.replace("Z", "+00:00"))
        except Exception:
            errors.append("invalid_event_ts")
        return errors


# --------------------------------------------------------------------- #
# Sample event generator (for tests / demos)
# --------------------------------------------------------------------- #

EVENT_TEMPLATES = [
    ("page_view",    {"page": "/feed"}),
    ("page_view",    {"page": "/home"}),
    ("page_view",    {"page": "/profile"}),
    ("click",        {"target": "like_button"}),
    ("click",        {"target": "comment_button"}),
    ("scroll",       {"depth_pct": "75"}),
    ("form_submit",  {"form_name": "signup"}),
    ("purchase",     {"revenue_usd": "29.99", "item_id": "sku_1234"}),
]

COUNTRIES = ["US", "IN", "BR", "GB", "DE", "JP", "FR", "CA"]
PLATFORMS = ["web", "ios", "android", "web", "ios"]


def generate_sample(n: int = 1000, bot_pct: float = 0.25, out: str = "events.jsonl"):
    rng = random.Random(42)
    n_bots = int(n * bot_pct)
    with open(out, "w") as f:
        for i in range(n):
            is_bot = i < n_bots
            name, props = rng.choice(EVENT_TEMPLATES)
            ev = ClickstreamEvent(
                event_id    = str(uuid.uuid4()),
                user_id     = f"user_{rng.randint(1, 500):06d}",
                event_ts    = datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z"),
                event_name  = name,
                session_id  = str(uuid.uuid4()),
                platform    = rng.choice(PLATFORMS),
                app_version = "12.4.0",
                country     = rng.choice(COUNTRIES),
                device_class= "mobile" if rng.random() < 0.7 else "desktop",
                user_agent  = "headless-chrome/91" if is_bot else "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)",
                properties  = props,
                context     = {"experiment_ids": "exp_feed_rank_v2,exp_home_redesign"},
            )
            f.write(ev.to_json() + "\n")
    print(f"Wrote {n} events to {out} ({bot_pct*100:.0f}% bots)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--count",  type=int, default=1000)
    p.add_argument("--bots",   type=float, default=0.25)
    p.add_argument("--out",    default="sample_data/events.jsonl")
    args = p.parse_args()
    generate_sample(args.count, args.bots, args.out)
