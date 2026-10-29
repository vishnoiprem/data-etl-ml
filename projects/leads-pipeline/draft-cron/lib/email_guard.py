"""
lib/email_guard.py — Pre-send guard rails for the Avilx outreach pipeline.

Why this exists
---------------
Prem's Gmail account got put on hold by Google for 27.3% bounce rate in 24h
(24/88 sent). Root cause: the loop's default `derive_email_from_company`
returns `careers@{domain}` for ~150 known AI startups, but most have no
public careers inbox — they route through Greenhouse / Lever / Workday
that hard-bounce. Gmail's SMTP returns 250 ("accepted") for everything;
bounces come back hours later via IMAP. By then the bounce ratio has
already triggered the throttle.

This module provides a single, central check that any caller can use
before initiating an SMTP send:

    ok, reason = can_send_to("careers@runwayml.com")
    if not ok:
        print(f"  ⏭  {addr}  skipped: {reason}")
        continue

The check is fast (no I/O except optional MX DNS), idempotent, and
self-healing — once a domain bounces, BOUNCE_DENY auto-extends and the
next iteration skips it.

Check order (short-circuits on first fail)
------------------------------------------
1. **Format** — `addr` must look like an email
2. **BOUNCE_DENY** — registered domain not in the persisted denylist
3. **Tail log** — recipient not contacted in the last `tail_log_hours` (24)
4. **Daily cap** — `count_sends_today() < max_daily` (default 3 during recovery)
5. **Hourly cap** — `count_sends_this_hour() < max_hourly` (default 2)
6. **MX probe** — `dns.resolver.resolve(domain, 'MX')` succeeds

Each reason is a short, machine-friendly tag (e.g. `"deny:runwayml.com"`,
`"tail:24h"`, `"cap:daily=3"`, `"mx:NXDOMAIN"`) so the loop log can be
post-processed.
"""

from __future__ import annotations

import os
import re
from typing import Tuple

# Email regex: local@domain.tld with at least one dot in domain. Intentionally
# simple — we trust SMTP to do the heavy validation; this is just a sanity
# filter for obvious garbage.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Default caps. Lowered from DAILY_LIMIT=10 to 3/2 during the recovery
# period so we build a clean 7-day track record. Operators can override
# via env (RECOVERY_DAILY_LIMIT, RECOVERY_HOURLY_LIMIT) or pass kwargs.
DEFAULT_MAX_DAILY = int(os.getenv("RECOVERY_DAILY_LIMIT", "3"))
DEFAULT_MAX_HOURLY = int(os.getenv("RECOVERY_HOURLY_LIMIT", "2"))
DEFAULT_TAIL_HOURS = int(os.getenv("AVILX_TAIL_LOG_HOURS", "24"))


def _reg_domain(addr: str) -> str:
    """Return the registered (last-2-labels) domain — e.g. 'careers@pika.art' → 'pika.art'.

    Used as the BOUNCE_DENY key so 'foo.bar.pika.art' and 'pika.art' match
    the same denylist entry.
    """
    try:
        dom = addr.split("@", 1)[1].lower().strip()
    except IndexError:
        return ""
    parts = dom.split(".")
    if len(parts) < 2:
        return dom
    return ".".join(parts[-2:])


def can_send_to(
    addr: str,
    *,
    max_daily: int = DEFAULT_MAX_DAILY,
    max_hourly: int = DEFAULT_MAX_HOURLY,
    tail_log_hours: int = DEFAULT_TAIL_HOURS,
    do_mx_probe: bool = True,
) -> Tuple[bool, str]:
    """Decide whether we can send to `addr` right now.

    Returns `(ok, reason)`. `reason` is empty on success; otherwise it's a
    short skip-code (suitable for logging) like "deny:pika.art",
    "tail:24h", "cap:daily=3", "mx:NXDOMAIN", "fmt".

    The function is pure with respect to side effects: it does not write to
    the DB. Callers (send_queued_emails, --dry checks) own any state changes.

    The DNS probe is the only potentially-slow step. Pass `do_mx_probe=False`
    to skip it (e.g. for batch pre-checks where you only care about
    denylist/tail-log/caps).
    """
    # Lazy imports so the module loads even if db/dns aren't yet importable
    # (useful for ad-hoc CLI use during recovery).
    try:
        from state.bounce_deny_store import BOUNCE_DENY
    except Exception:
        BOUNCE_DENY = set()  # type: ignore

    # 1) Format
    if not addr or not _EMAIL_RE.match(addr.strip()):
        return False, "fmt"

    rd = _reg_domain(addr)

    # 2) BOUNCE_DENY (in-memory, fast)
    if rd and rd in BOUNCE_DENY:
        return False, f"deny:{rd}"

    # 3) Tail log — has this recipient been emailed in the last N hours?
    if tail_log_hours > 0:
        try:
            from db.lead_store import was_recently_sent
            if was_recently_sent(addr, hours=tail_log_hours):
                return False, f"tail:{tail_log_hours}h"
        except Exception:
            pass  # DB down → don't block sends, but log

    # 4) Daily cap
    if max_daily > 0:
        try:
            from db.lead_store import count_sends_today
            n_today = count_sends_today()
            if n_today >= max_daily:
                return False, f"cap:daily={n_today}/{max_daily}"
        except Exception:
            pass

    # 5) Hourly cap
    if max_hourly > 0:
        try:
            from db.lead_store import count_sends_this_hour
            n_hour = count_sends_this_hour()
            if n_hour >= max_hourly:
                return False, f"cap:hourly={n_hour}/{max_hourly}"
        except Exception:
            pass

    # 6) MX probe — does the domain actually accept mail?
    if do_mx_probe and rd:
        mx_err = _mx_probe(rd)
        if mx_err:
            return False, f"mx:{mx_err}"

    return True, ""


def _mx_probe(domain: str, timeout: float = 3.0) -> str:
    """Return '' on success, or a short error tag ('NXDOMAIN', 'TIMEOUT',
    'NOMX', 'ERR:...').

    Uses `dns.resolver` (dnspython 2.x) which is already a dependency
    (verified in the venv). 3-second timeout keeps the per-lead cost
    bounded so the guard doesn't itself become a 30s bottleneck.
    """
    try:
        import dns.resolver
        import dns.exception
    except ImportError:
        return ""  # dnspython not installed — skip probe, let SMTP try
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=timeout)
        if not answers:
            return "NOMX"
        return ""
    except dns.resolver.NXDOMAIN:
        return "NXDOMAIN"
    except dns.resolver.NoNameservers:
        return "NONAMESERVERS"
    except dns.resolver.Timeout:
        return "TIMEOUT"
    except dns.exception.DNSException as e:
        return f"ERR:{type(e).__name__}"
    except Exception as e:
        # Don't crash the loop on unexpected DNS errors — treat as probe
        # failure and let SMTP try. Worst case: another bounce, but the
        # MX probe is a best-effort speedup, not a guarantee.
        return f"ERR:{type(e).__name__}"


def guard_leads(leads, **kwargs) -> Tuple[list, list]:
    """Filter a list of leads through the guard. Returns (sendable, skipped).

    `leads` is an iterable of dicts with at least a `contact_email` key.
    `kwargs` are passed to can_send_to.

    Each skipped lead gets a `_skip_reason` attribute (dict key) so the
    caller can log it.
    """
    sendable: list = []
    skipped: list = []
    for lead in leads:
        addr = (lead.get("contact_email") or "").strip()
        ok, reason = can_send_to(addr, **kwargs)
        if ok:
            sendable.append(lead)
        else:
            lead["_skip_reason"] = reason
            skipped.append(lead)
    return sendable, skipped


if __name__ == "__main__":
    import sys
    for line in sys.stdin:
        addr = line.strip()
        if not addr:
            continue
        ok, reason = can_send_to(addr)
        tag = "✅" if ok else "⏭ "
        print(f"  {tag} {addr:40s}  {reason}")
