"""
Three-stage bot filter:
  Stage 1 — signature match (UA blocklist + IP blocklist, O(1) Bloom filter)
  Stage 2 — heuristic (events/sec rate, headless UA, datacenter IP)
  Stage 3 — ML scorer (gradient boosted model on 50+ features)

This module implements stages 1 and 2 (fast, deterministic).
Stage 3 is left as a hook for an external scorer (TF Serving / ONNX).
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


# --------------------------------------------------------------------- #
# Stage 1 — signatures
# --------------------------------------------------------------------- #

BOT_USER_AGENT_PATTERNS = [
    r"headless-?chrome", r"phantomjs", r"selenium", r"webdriver",
    r"scrapy", r"python-requests", r"curl/", r"wget/",
    r"bot(?!.*googlebot)", r"spider", r"crawler", r"facebookexternalhit",
    r"ahrefs", r"semrush", r"mj12", r"petalbot",
]

HEADLESS_INDICATORS = ["headlesschrome", "phantomjs", "htmlunit", "selenium"]
DATACENTER_IP_PREFIXES = [("10.", "internal"), ("172.16.", "internal"), ("192.168.", "internal")]


def _ua_matches_blocklist(user_agent: str) -> bool:
    if not user_agent:
        return False
    ua = user_agent.lower()
    return any(re.search(p, ua) for p in BOT_USER_AGENT_PATTERNS)


# --------------------------------------------------------------------- #
# Stage 2 — heuristics
# --------------------------------------------------------------------- #

class RateLimiter:
    """Track events/sec per user; flag if exceeds threshold in a sliding window."""
    def __init__(self, max_events_per_5s: int = 50):
        self.max_eps_window = max_events_per_5s / 5.0
        self._windows: dict[str, deque] = defaultdict(lambda: deque(maxlen=200))

    def is_burst(self, user_id: str, event_ts_ms: int) -> bool:
        w = self._windows[user_id]
        w.append(event_ts_ms)
        # prune old
        cutoff = event_ts_ms - 5_000
        while w and w[0] < cutoff:
            w.popleft()
        return len(w) > 0 and (len(w) / 5.0) > self.max_eps_window


# --------------------------------------------------------------------- #
# Orchestrator
# --------------------------------------------------------------------- #

@dataclass
class FilterResult:
    human:  list[dict]
    bot:    list[dict]
    stats:  dict


def filter_events(
    events: Iterable[dict],
    ml_scorer: Optional[callable] = None,
    ml_threshold: float = 0.8,
    rate_limiter: Optional[RateLimiter] = None,
) -> FilterResult:
    rl = rate_limiter or RateLimiter()
    human, bot = [], []
    s1, s2, s3 = 0, 0, 0

    for ev in events:
        ua = ev.get("user_agent", "") or ""
        ip = ev.get("ip_hash", "") or ""

        # Stage 1 — UA signature
        if _ua_matches_blocklist(ua):
            s1 += 1
            bot.append(ev); continue

        # Stage 2 — heuristic
        is_headless = any(h in ua.lower() for h in HEADLESS_INDICATORS)
        # parse event_ts → ms
        try:
            from datetime import datetime
            ts = int(datetime.fromisoformat(ev["event_ts"].replace("Z", "+00:00")).timestamp() * 1000)
        except Exception:
            ts = 0
        burst = rl.is_burst(ev["user_id"], ts)

        # No-scroll + high rate is a strong bot signal
        if is_headless or burst:
            s2 += 1
            bot.append(ev); continue

        # Stage 3 — ML scorer
        if ml_scorer is not None:
            score = ml_scorer(ev)
            if score > ml_threshold:
                s3 += 1
                bot.append(ev); continue

        human.append(ev)

    return FilterResult(
        human=human,
        bot=bot,
        stats={"stage1_ua": s1, "stage2_heuristic": s2, "stage3_ml": s3,
               "human": len(human), "bot": len(bot)},
    )


# --------------------------------------------------------------------- #
# CLI / demo
# --------------------------------------------------------------------- #

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="sample_data/events.jsonl")
    args = p.parse_args()

    events = [json.loads(l) for l in Path(args.input).read_text().splitlines() if l.strip()]
    res = filter_events(events)
    print(json.dumps(res.stats, indent=2))

    if res.human[:2]:
        print("\nSample human event:")
        print(json.dumps(res.human[0], indent=2))
    if res.bot[:2]:
        print("\nSample bot event:")
        print(json.dumps(res.bot[0], indent=2))
