"""
Dedup keyed state with TTL — the Flink operator, modelled in plain Python.

No Spark here on purpose. The dedup operator is the piece of this pipeline most
likely to be drawn on a whiteboard, and its correctness is about STATE and
WATERMARKS, not about a query engine. Stripping the engine away makes the four
decisions visible:

  1. state key      = (user_id, ad_id)
  2. state value    = first_seen_ts        <- FIRST, not last. See below.
  3. eviction       = watermark - 60s      <- what bounds the state
  4. late events    = side output, never silently dropped

THE WINDOW SEMANTICS DECISION (ask the interviewer, then state your choice):

  FIXED-FROM-FIRST (implemented here, and correct for billing)
      Window opens at the first click and closes 60s later, regardless of what
      happens in between. A bot clicking every 59s keeps getting billed -- once
      per window it opens, so roughly every other click.

  SLIDING-FROM-LAST (the tempting bug)
      Every click extends the window. A bot clicking every 59s is deduped
      FOREVER and billed exactly once, ever. You have just given away
      unlimited free clicks to the most patient attacker.

  The spec says "same user + same ad within 60 seconds = 1 click", which reads
  as fixed-from-first. Both are implemented below and the divergence is
  asserted, because this is the subtle one.

WHY NOT A SET / SELECT DISTINCT:
  An unbounded dedup set over a year of clicks is ~21 TiB of state (see
  python/capacity_model.py). The job dies. The 60s TTL is what makes the state
  a few hundred MiB instead.
"""

DEDUP_WINDOW_MS = 60_000
ALLOWED_LATENESS_MS = 30_000     # how far past the watermark we still accept


class DedupOperator:
    """Keyed-state dedup with watermark-driven eviction.

    Mirrors a Flink KeyedProcessFunction with state TTL, or Spark's
    dropDuplicatesWithinWatermark(). Deliberately NOT a plain set.
    """

    def __init__(self, window_ms=DEDUP_WINDOW_MS, sliding=False,
                 allowed_lateness_ms=ALLOWED_LATENESS_MS):
        self.window_ms = window_ms
        self.sliding = sliding          # True = the buggy sliding-from-last
        self.allowed_lateness_ms = allowed_lateness_ms
        self._state = {}                # (user_id, ad_id) -> window_open_ts
        self.watermark = 0
        self.stats = dict(emitted=0, duplicate=0, late=0, evicted=0)
        self.side_output_late = []

    # -- watermark ------------------------------------------------------------

    def advance_watermark(self, event_ts):
        """Watermarks only move FORWARD. An out-of-order event must not rewind
        it, or eviction becomes non-deterministic across restarts."""
        self.watermark = max(self.watermark, event_ts)
        self._evict()

    def _evict(self):
        """Drop state whose window closed before the watermark. This is the
        single line that turns unbounded state into bounded state."""
        cutoff = self.watermark - self.window_ms
        stale = [k for k, opened in self._state.items() if opened < cutoff]
        for k in stale:
            del self._state[k]
        self.stats["evicted"] += len(stale)

    # -- the operator ---------------------------------------------------------

    def process(self, event):
        """Return 'emit' | 'duplicate' | 'late'."""
        key = (event["user_id"], event["ad_id"])
        ts = event["event_ts"]

        # Too late to judge: our state for this window is already evicted, so
        # we CANNOT know whether this is a duplicate. Route it out rather than
        # guess -- guessing 'emit' risks double-billing, guessing 'duplicate'
        # risks dropping revenue. The batch layer decides.
        if ts < self.watermark - self.window_ms - self.allowed_lateness_ms:
            self.stats["late"] += 1
            self.side_output_late.append(event)
            return "late"

        self.advance_watermark(ts)
        opened = self._state.get(key)

        if opened is not None and ts - opened < self.window_ms:
            if self.sliding:
                self._state[key] = ts       # the bug: extends the window
            self.stats["duplicate"] += 1
            return "duplicate"

        self._state[key] = ts
        self.stats["emitted"] += 1
        return "emit"

    @property
    def state_size(self):
        return len(self._state)


# ============================================================ self-verification
if __name__ == "__main__":

    def ev(user, ad, ts):
        return {"user_id": user, "ad_id": ad, "event_ts": ts}

    # -- the basic case -----------------------------------------------------
    d = DedupOperator()
    assert d.process(ev("u1", "a1", 0)) == "emit"
    assert d.process(ev("u1", "a1", 30_000)) == "duplicate"     # 30s in
    assert d.process(ev("u1", "a1", 59_999)) == "duplicate"     # 1ms before close
    assert d.process(ev("u1", "a1", 60_000)) == "emit"          # exactly 60s -> new
    print("[PASS] 60s window is half-open [open, open+60s): 59,999ms is a duplicate, "
          "60,000ms\n       opens a new window")

    # -- different ad, same user is NOT a duplicate -------------------------
    d = DedupOperator()
    assert d.process(ev("u1", "a1", 0)) == "emit"
    assert d.process(ev("u1", "a2", 100)) == "emit"
    assert d.process(ev("u2", "a1", 100)) == "emit"
    print("[PASS] the key is (user_id, ad_id) -- same user/different ad and "
          "different user/same ad\n       both emit")

    # -- THE SEMANTICS TRAP: a patient bot clicking every 59s ---------------
    # 10 clicks, each 59s after the last, over ~9 minutes.
    patient_bot = [ev("bot", "a1", i * 59_000) for i in range(10)]

    fixed = DedupOperator(sliding=False)
    for e in patient_bot:
        fixed.process(e)

    sliding = DedupOperator(sliding=True)
    for e in patient_bot:
        sliding.process(e)

    assert fixed.stats["emitted"] == 5, fixed.stats
    assert sliding.stats["emitted"] == 1, sliding.stats
    print(f"[PASS] patient bot, 10 clicks at 59s intervals over ~9 minutes:")
    print(f"         fixed-from-first  -> {fixed.stats['emitted']:>2} billed  (correct)")
    print(f"         sliding-from-last -> {sliding.stats['emitted']:>2} billed  "
          "(unlimited free clicks)")
    print("       -> fixed-from-first bills once per 60s window, so consecutive")
    print("          59s-apart clicks ALTERNATE: the first opens a window, the")
    print("          second falls inside it, the third opens the next one.")
    print("       -> sliding-from-last is the bug: each click extends the window,")
    print("          so the attacker is deduped forever and billed once, ever.")

    # -- a real human double-click IS caught by both ------------------------
    human = [ev("u9", "a9", 0), ev("u9", "a9", 180)]     # 180ms apart
    for mode, flag in (("fixed", False), ("sliding", True)):
        op = DedupOperator(sliding=flag)
        for e in human:
            op.process(e)
        assert op.stats["emitted"] == 1, (mode, op.stats)
    print("[PASS] a genuine 180ms double-click collapses to 1 under both semantics "
          "-- the\n       variants only diverge on sustained low-rate abuse")

    # -- state is BOUNDED by the watermark ----------------------------------
    d = DedupOperator()
    for i in range(1_000):                       # 1000 distinct users, t=0
        d.process(ev(f"u{i}", "a1", 0))
    assert d.state_size == 1_000, d.state_size
    print(f"[PASS] state holds {d.state_size:,} keys while the window is open")

    d.advance_watermark(200_000)                 # jump 200s forward
    assert d.state_size == 0, d.state_size
    assert d.stats["evicted"] == 1_000
    print(f"[PASS] watermark advance to 200s evicted all {d.stats['evicted']:,} keys "
          "-> state\n       is bounded by the window, not by total traffic")

    # Contrast with an unbounded set, which is the naive implementation.
    naive = set()
    for i in range(1_000):
        naive.add((f"u{i}", "a1"))
    assert len(naive) == 1_000
    print("[PASS] an unbounded set still holds 1,000 keys after the same advance "
          "-- over a\n       year that is ~21 TiB and the job dies")

    # -- watermarks never rewind -------------------------------------------
    d = DedupOperator()
    d.process(ev("u1", "a1", 500_000))
    wm_high = d.watermark
    d.process(ev("u2", "a2", 100_000))           # out of order, still in range
    assert d.watermark == wm_high, (d.watermark, wm_high)
    print(f"[PASS] an out-of-order event at 100s did not rewind the watermark "
          f"from {wm_high:,}\n       -- eviction stays deterministic across restarts")

    # -- late events go to a side output, never silently dropped -----------
    d = DedupOperator()
    d.process(ev("u1", "a1", 0))
    d.advance_watermark(500_000)                 # watermark now 500s
    verdict = d.process(ev("u1", "a1", 1_000))   # 499s late, past lateness budget
    assert verdict == "late", verdict
    assert len(d.side_output_late) == 1
    print("[PASS] an event 499s late is routed to the side output, NOT dropped and "
          "NOT\n       guessed -- the batch layer reconciles it")

    # An event inside the lateness budget is still judged normally.
    d = DedupOperator()
    d.process(ev("u1", "a1", 100_000))
    d.advance_watermark(150_000)
    assert d.process(ev("u1", "a1", 120_000)) == "duplicate"
    print("[PASS] an event 30s late but within the lateness budget is still "
          "deduped correctly")

    # -- realistic mixed stream, end to end ---------------------------------
    d = DedupOperator()
    stream = []
    stream += [ev("u1", "a1", 1_000), ev("u1", "a1", 1_200)]       # double-click
    stream += [ev(f"h{i}", "a1", 2_000 + i) for i in range(100)]   # 100 humans
    stream += [ev("bot", "a1", 3_000 + i * 200) for i in range(50)]  # 50 in 10s
    stream += [ev("u1", "a1", 70_000)]                             # legit re-click
    for e in stream:
        d.process(e)

    assert d.stats["emitted"] == 103, d.stats
    assert d.stats["duplicate"] == 50, d.stats
    total = d.stats["emitted"] + d.stats["duplicate"] + d.stats["late"]
    assert total == len(stream), (total, len(stream))
    print(f"[PASS] mixed stream of {len(stream)} events -> {d.stats['emitted']} billable, "
          f"{d.stats['duplicate']} deduped, {d.stats['late']} late")
    print(f"       every input accounted for ({total} = {len(stream)}) -- the "
          "operator conserves events,\n       which is the invariant billing "
          "reconciliation depends on")

    print("\n[PASS] dedup operator verified: bounded state, forward-only watermarks, "
          "fixed-from-first\n       windows, and late events surfaced rather than "
          "guessed")
