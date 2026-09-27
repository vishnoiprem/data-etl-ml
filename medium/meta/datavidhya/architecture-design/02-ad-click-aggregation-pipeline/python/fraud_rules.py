"""
Fraud detection — TIER 1 (inline, deterministic, microseconds).

Runs at the edge collector, BEFORE the event reaches Kafka, because every event
that gets past here is a candidate for billing.

THE TIERING IS THE ANSWER. You cannot do all fraud inline and you cannot defer
it all:

  TIER 1 (this file)   µs         deterministic, single-event or small-window
                                  -> DROP before counting
  TIER 2 (async ML)    min-hours  cross-event, needs 10k events to see a farm
                                  -> RETROACTIVE invalidation via verdicts

A candidate who proposes only tier 1 bills click farms. A candidate who proposes
only tier 2 either misses the 10s SLO or bills fraud and refunds later. Say both.

WHY THIS SITS UPSTREAM OF COUNTING:
  1B clicks/day x 15% fraud x $0.50 CPC = $75M/day of mis-billing risk.
  See python/capacity_model.py for the full derivation.

DESIGN RULE, stated explicitly:
  Every ambiguous click fails toward NOT BILLING. A missed real click costs a
  fraction of a cent. A double-billed click costs a chargeback, an audit, and
  an advertiser. The asymmetry is enormous and it should drive every threshold
  in this file.
"""
from collections import deque

# ---------------------------------------------------------------- tier-1 rules
# Each is O(1) or O(small window) so it can run synchronously per event.

DATACENTER_ASN = {  # abbreviated; in production this is a maintained feed
    15169: "Google Cloud",
    16509: "AWS",
    8075: "Azure",
    14061: "DigitalOcean",
    16276: "OVH",
}

BOT_UA_MARKERS = (
    "bot", "crawler", "spider", "headless", "phantomjs", "puppeteer",
    "selenium", "python-requests", "curl/", "wget/",
)

# Thresholds. These are the numbers an interviewer will push on, so each one
# carries the reasoning that sets it.
MAX_CLICKS_PER_USER_PER_SEC = 3      # human double-click is ~2; 3 is generous
MAX_CLICKS_PER_IP_PER_MIN = 60       # shared NAT (office, mobile carrier) is
                                     # real, so this must not be too tight
MIN_MS_BETWEEN_IMPRESSION_AND_CLICK = 50   # <50ms means no human saw the ad
MAX_MS_BETWEEN_IMPRESSION_AND_CLICK = 3_600_000  # 1h: stale/replayed impression


class Tier1FraudFilter:
    """Inline, per-event fraud filter with bounded state.

    State is bounded by the rate-limit windows, exactly like the dedup state in
    pyspark/dedup_clicks.py -- unbounded counters would be the same mistake as
    an unbounded DISTINCT.
    """

    def __init__(self):
        self._user_clicks = {}   # user_id -> deque[ts_ms] within 1s
        self._ip_clicks = {}     # ip      -> deque[ts_ms] within 60s

    # -- individual rules -----------------------------------------------------

    @staticmethod
    def is_datacenter_ip(asn):
        """Ads are served to humans on consumer networks. A click from a cloud
        ASN is a bot with ~no false-positive risk, so it is a safe hard drop."""
        return asn in DATACENTER_ASN

    @staticmethod
    def is_bot_user_agent(user_agent):
        ua = (user_agent or "").lower()
        return any(marker in ua for marker in BOT_UA_MARKERS)

    @staticmethod
    def is_malformed(event):
        """A missing required field means we cannot attribute or bill it
        anyway, so dropping is strictly correct."""
        required = ("event_id", "ad_id", "campaign_id", "user_id", "event_ts")
        return any(event.get(f) in (None, "") for f in required)

    @staticmethod
    def impression_click_gap_implausible(event):
        """Time-to-click is the single strongest cheap signal. Too fast means
        no human perceived the ad; too slow means a replayed impression id."""
        gap = event.get("ms_since_impression")
        if gap is None:
            return False          # no impression context -> cannot judge here
        return (gap < MIN_MS_BETWEEN_IMPRESSION_AND_CLICK
                or gap > MAX_MS_BETWEEN_IMPRESSION_AND_CLICK)

    def user_rate_exceeded(self, user_id, ts_ms):
        dq = self._user_clicks.setdefault(user_id, deque())
        dq.append(ts_ms)
        while dq and ts_ms - dq[0] >= 1_000:
            dq.popleft()
        return len(dq) > MAX_CLICKS_PER_USER_PER_SEC

    def ip_rate_exceeded(self, ip, ts_ms):
        dq = self._ip_clicks.setdefault(ip, deque())
        dq.append(ts_ms)
        while dq and ts_ms - dq[0] >= 60_000:
            dq.popleft()
        return len(dq) > MAX_CLICKS_PER_IP_PER_MIN

    # -- the filter -----------------------------------------------------------

    def evaluate(self, event):
        """Return (verdict, reason). verdict is 'accept' or 'reject'.

        Order matters: cheapest and most certain checks first, so the common
        path is a few comparisons.
        """
        if self.is_malformed(event):
            return "reject", "malformed"
        if self.is_datacenter_ip(event.get("asn")):
            return "reject", f"datacenter_ip:{DATACENTER_ASN[event['asn']]}"
        if self.is_bot_user_agent(event.get("user_agent")):
            return "reject", "bot_user_agent"
        if self.impression_click_gap_implausible(event):
            return "reject", "implausible_click_latency"
        if self.user_rate_exceeded(event["user_id"], event["event_ts"]):
            return "reject", "user_rate_limit"
        if self.ip_rate_exceeded(event.get("ip", "0.0.0.0"), event["event_ts"]):
            return "reject", "ip_rate_limit"
        return "accept", "ok"


# ============================================================ self-verification
if __name__ == "__main__":

    def ev(**kw):
        base = dict(event_id="e1", ad_id="a1", campaign_id="c1", user_id="u1",
                    event_ts=1_000_000, ip="203.0.113.7", asn=7922,
                    user_agent="Mozilla/5.0 (iPhone)", ms_since_impression=2_500)
        base.update(kw)
        return base

    f = Tier1FraudFilter()

    # -- each rule fires on its own case ------------------------------------
    cases = [
        ("clean human click",          ev(),                                   "accept"),
        ("missing campaign_id",        ev(campaign_id=None),                   "reject"),
        ("AWS datacenter IP",          ev(asn=16509),                          "reject"),
        ("headless chrome UA",         ev(user_agent="HeadlessChrome/120"),    "reject"),
        ("python-requests UA",         ev(user_agent="python-requests/2.31"),  "reject"),
        ("click 12ms after impression", ev(ms_since_impression=12),            "reject"),
        ("click 2h after impression",  ev(ms_since_impression=7_200_000),      "reject"),
    ]
    for label, event, want in cases:
        got, reason = Tier1FraudFilter().evaluate(event)
        assert got == want, f"{label}: expected {want}, got {got} ({reason})"
        print(f"[PASS] {label:<30} -> {got:<7} ({reason})")

    # -- user rate limit: 3 allowed in 1s, the 4th is rejected --------------
    f = Tier1FraudFilter()
    verdicts = [f.evaluate(ev(event_id=f"e{i}", event_ts=1_000_000 + i * 100))[0]
                for i in range(5)]
    assert verdicts == ["accept", "accept", "accept", "reject", "reject"], verdicts
    print(f"[PASS] user rate limit: 5 clicks in 400ms -> "
          f"{verdicts.count('accept')} accepted, {verdicts.count('reject')} rejected")

    # ...but the SAME user a second later is fine: the window slides.
    later = f.evaluate(ev(event_id="e99", event_ts=1_002_000))[0]
    assert later == "accept", later
    print("[PASS] the window slides -- same user 2s later is accepted, so a "
          "legitimate\n       returning user is not permanently banned")

    # -- shared NAT must NOT be over-blocked --------------------------------
    # 50 different users behind one office IP in a minute is normal traffic.
    f = Tier1FraudFilter()
    nat = [f.evaluate(ev(event_id=f"n{i}", user_id=f"nat_u{i}",
                         ip="198.51.100.1", event_ts=1_000_000 + i * 1_000))[0]
           for i in range(50)]
    assert all(v == "accept" for v in nat), nat.count("reject")
    print("[PASS] 50 distinct users behind one NAT IP all accepted -- the IP limit "
          "is\n       set for shared egress, not per-household")

    # ...but 70 in the same minute trips it.
    f = Tier1FraudFilter()
    farm = [f.evaluate(ev(event_id=f"k{i}", user_id=f"farm_u{i}",
                          ip="198.51.100.9", event_ts=1_000_000 + i * 500))[0]
            for i in range(70)]
    assert farm.count("reject") == 10, farm.count("reject")
    print(f"[PASS] 70 clicks from one IP in 35s -> {farm.count('reject')} rejected "
          "past the 60/min limit")

    # -- what tier 1 CANNOT catch (the reason tier 2 exists) ----------------
    # A click farm: 10k real devices, real UAs, residential IPs, human-plausible
    # latency, one click each. Every single event passes tier 1.
    f = Tier1FraudFilter()
    farm_events = [ev(event_id=f"cf{i}", user_id=f"device_{i}",
                      ip=f"192.0.2.{i % 254 + 1}",
                      event_ts=1_000_000 + i * 37,
                      ms_since_impression=1_800 + (i % 900))
                   for i in range(10_000)]
    accepted = sum(1 for e in farm_events if f.evaluate(e)[0] == "accept")
    assert accepted > 9_000, accepted
    print(f"[PASS] click farm of 10,000 distinct devices: {accepted:,} pass tier 1")
    print("       -> INDISTINGUISHABLE from real traffic per-event. Only a")
    print("          cross-event model sees the coordination. THIS is tier 2,")
    print("          and it is why billing waits for the batch layer.")

    # -- the money math -----------------------------------------------------
    CLICKS_PER_DAY, CPC = 1_000_000_000, 0.50
    for rate in (0.10, 0.15, 0.20):
        print(f"[PASS] at {rate:.0%} fraud: ${CLICKS_PER_DAY * rate * CPC / 1e6:,.0f}M/day "
              f"(${CLICKS_PER_DAY * rate * CPC * 365 / 1e9:,.1f}B/yr) of mis-billing risk")

    # -- the asymmetry that sets the thresholds -----------------------------
    cost_missed_click = CPC                      # lost revenue on one click
    cost_double_billed = CPC + 25.00             # + chargeback/dispute handling
    ratio = cost_double_billed / cost_missed_click
    assert ratio > 50
    print(f"[PASS] a double-billed click costs ~{ratio:.0f}x a missed one "
          "-> every threshold\n       above is tuned to fail toward NOT billing")

    print("\n[PASS] tier-1 filter verified: catches what is cheap and certain, "
          "and demonstrably\n       misses what needs cross-event context")
