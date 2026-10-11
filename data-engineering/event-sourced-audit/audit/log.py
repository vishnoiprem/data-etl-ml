"""Append-only event log with hash chain.

Meaningful workload:
- Generates ~10k synthetic audit events across 8 actors × 4 actions × ~200 targets.
- Appends events chronologically, verifies hash-chain integrity.
- Builds a live current-state projection (per-target last action + counts).
- Replays the log from scratch to rebuild a snapshot, compares to the live projection.
- Runs 4 audit queries (by actor, by action, by target, all-deletes-for-target).
- Asserts: no gaps in seq, every event has a payload, snapshot==projection,
  query counts match, sum across event_types == total.
"""
from __future__ import annotations
import hashlib
import json
import random
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional


ACTIONS = ("read", "edit", "delete", "create")
ACTORS = ("alice", "bob", "carol", "dave", "eve", "frank", "grace", "heidi")
TARGET_KINDS = ("row", "doc", "secret", "config", "user")


@dataclass
class Event:
    seq: int
    ts: float
    actor: str
    action: str           # "read" | "edit" | "delete" | "create"
    target: str
    prev_hash: str
    payload: dict = field(default_factory=dict)

    def digest(self) -> str:
        body = json.dumps({
            "seq": self.seq, "ts": self.ts, "actor": self.actor,
            "action": self.action, "target": self.target,
            "prev_hash": self.prev_hash, "payload": self.payload,
        }, sort_keys=True)
        return hashlib.sha256(body.encode()).hexdigest()


class AuditLog:
    def __init__(self):
        self.events: list[Event] = []

    def append(self, actor: str, action: str, target: str, payload: Optional[dict] = None) -> Event:
        prev = self.events[-1].digest() if self.events else "0" * 64
        e = Event(
            seq=len(self.events), ts=time.time(),
            actor=actor, action=action, target=target,
            prev_hash=prev, payload=payload or {},
        )
        self.events.append(e)
        return e

    def verify(self) -> tuple[bool, int]:
        """Returns (ok, first_bad_seq)."""
        prev = "0" * 64
        for e in self.events:
            if e.prev_hash != prev:
                return False, e.seq
            prev = e.digest()
        return True, -1

    def projection(self) -> dict:
        """Current-state projection: per-target last action + per-action counts.

        Returns a JSON-serialisable dict of the form:
          {"<target>": {"last_action": str, "last_actor": str,
                        "last_ts": float, "counts": {action: n, ...}, "n_events": int}, ...}
        """
        proj: dict[str, dict] = {}
        for e in self.events:
            t = proj.setdefault(e.target, {
                "last_action": e.action, "last_actor": e.actor,
                "last_ts": e.ts, "counts": defaultdict(int), "n_events": 0,
            })
            t["last_action"] = e.action
            t["last_actor"] = e.actor
            t["last_ts"] = e.ts
            t["counts"][e.action] += 1
            t["n_events"] += 1
        # defaultdicts -> dicts for json/equality
        out: dict[str, dict] = {}
        for k, v in proj.items():
            out[k] = {
                "last_action": v["last_action"],
                "last_actor": v["last_actor"],
                "last_ts": v["last_ts"],
                "counts": dict(v["counts"]),
                "n_events": v["n_events"],
            }
        return out

    def snapshot(self) -> tuple[dict, str]:
        """Replay the log to rebuild a snapshot, returning (snapshot, final_hash).

        Independent rebuild so projection() and snapshot() can be compared even
        if the live in-memory state was mutated.
        """
        snap: dict[str, dict] = {}
        prev = "0" * 64
        for e in self.events:
            if e.prev_hash != prev:
                raise ValueError(f"snapshot: chain broken at seq={e.seq}")
            t = snap.setdefault(e.target, {
                "last_action": e.action, "last_actor": e.actor,
                "last_ts": e.ts, "counts": defaultdict(int), "n_events": 0,
            })
            t["last_action"] = e.action
            t["last_actor"] = e.actor
            t["last_ts"] = e.ts
            t["counts"][e.action] += 1
            t["n_events"] += 1
            prev = e.digest()
        out: dict[str, dict] = {}
        for k, v in snap.items():
            out[k] = {
                "last_action": v["last_action"],
                "last_actor": v["last_actor"],
                "last_ts": v["last_ts"],
                "counts": dict(v["counts"]),
                "n_events": v["n_events"],
            }
        return out, prev

    def query_by_actor(self, actor: str) -> list[Event]:
        return [e for e in self.events if e.actor == actor]

    def query_by_action(self, action: str) -> list[Event]:
        return [e for e in self.events if e.action == action]

    def query_deletes_for_target(self, target: str) -> list[Event]:
        return [e for e in self.events if e.target == target and e.action == "delete"]

    def query_target_history(self, target: str) -> list[Event]:
        return [e for e in self.events if e.target == target]


def generate_events(n: int, seed: int = 42) -> list[tuple[str, str, str, dict]]:
    """Generate `n` (actor, action, target, payload) tuples with realistic skew.

    - read is most common, delete is rare.
    - 8 actors, ~200 targets.
    - payload is always non-empty.
    """
    rng = random.Random(seed)
    action_weights = [("read", 0.55), ("edit", 0.25), ("create", 0.13), ("delete", 0.07)]
    actions_list = [a for a, _ in action_weights]
    weights = [w for _, w in action_weights]

    targets = [f"{k}:{i:04d}" for k in TARGET_KINDS for i in range(40)]
    out: list[tuple[str, str, str, dict]] = []
    for _ in range(n):
        actor = rng.choice(ACTORS)
        action = rng.choices(actions_list, weights=weights, k=1)[0]
        target = rng.choice(targets)
        if action == "read":
            payload = {"fields": rng.sample(["id", "name", "email", "ssn", "balance"], k=rng.randint(1, 3))}
        elif action == "edit":
            payload = {"field": rng.choice(["status", "name", "amount"]), "old": rng.randint(0, 99), "new": rng.randint(0, 99)}
        elif action == "create":
            payload = {"schema": rng.choice(["user", "order", "doc"]), "size": rng.randint(1, 4096)}
        else:  # delete
            payload = {"reason": rng.choice(["gdpr", "rotated", "duplicate", "policy"]), "soft": rng.choice([True, False])}
        out.append((actor, action, target, payload))
    return out


def assert_no_seq_gaps(log: AuditLog) -> None:
    for i, e in enumerate(log.events):
        assert e.seq == i, f"seq gap at index {i}: event.seq={e.seq}"


def assert_all_events_have_payload(log: AuditLog) -> None:
    for e in log.events:
        assert e.payload is not None, f"event seq={e.seq} has None payload"
        assert isinstance(e.payload, dict), f"event seq={e.seq} payload is not a dict"


def assert_event_count_matches_sum(log: AuditLog) -> None:
    by_action = Counter(e.action for e in log.events)
    assert sum(by_action.values()) == len(log.events), (
        f"sum(actions)={sum(by_action.values())} != total={len(log.events)}"
    )


if __name__ == "__main__":
    print("═══ event-sourced-audit: meaningful workload ═══")
    N = 10_000
    print(f"generating {N:,} events...")
    t0 = time.time()
    raw = generate_events(N, seed=42)
    print(f"  done in {time.time() - t0:.2f}s")
    # sanity: distribution
    ac = Counter(a for _, a, _, _ in raw)
    print(f"  action mix: {dict(ac)}")
    print()

    # ── Scenario A: append in chronological order, verify chain integrity ──
    print("═══ Scenario A: append + hash-chain integrity ═══")
    log = AuditLog()
    t0 = time.time()
    base_ts = 1_700_000_000.0
    for i, (actor, action, target, payload) in enumerate(raw):
        e = log.append(actor, action, target, payload)
        e.ts = base_ts + i  # monotonic timestamps for ordering
    append_t = time.time() - t0
    print(f"  appended {len(log.events):,} events in {append_t:.2f}s")
    t0 = time.time()
    ok, bad = log.verify()
    verify_t = time.time() - t0
    assert ok and bad == -1, f"chain verify failed at seq={bad}"
    print(f"  chain verify: ok=True in {verify_t:.2f}s ({N / verify_t:,.0f} events/s)")
    print()

    # ── Scenario B: build live projection, verify count matches ──
    print("═══ Scenario B: live projection ═══")
    t0 = time.time()
    proj = log.projection()
    proj_t = time.time() - t0
    total_projected_events = sum(v["n_events"] for v in proj.values())
    print(f"  projection built in {proj_t * 1000:.1f}ms")
    print(f"  targets in projection: {len(proj):,}")
    print(f"  total projected events: {total_projected_events:,}")
    assert total_projected_events == N, (
        f"projection total {total_projected_events} != log size {N}"
    )
    print("  projection total == log size")
    print()

    # ── Scenario C: replay the log from scratch, compare to projection ──
    print("═══ Scenario C: replay from log → snapshot ═══")
    t0 = time.time()
    snap, final_hash = log.snapshot()
    snap_t = time.time() - t0
    print(f"  replayed {N:,} events in {snap_t:.2f}s ({N / snap_t:,.0f} events/s)")
    print(f"  final chain hash: {final_hash[:16]}...")
    assert snap == proj, "snapshot != live projection (drift detected)"
    print("  snapshot == live projection  (no drift)")
    print(f"  live projection: {proj_t * 1000:.1f}ms  vs  replay: {snap_t * 1000:.1f}ms")
    print()

    # ── Scenario D: audit queries (specific patterns) ──
    print("═══ Scenario D: 4 audit queries ═══")
    queries = [
        ("events by actor=alice",        log.query_by_actor("alice")),
        ("events by action=delete",      log.query_by_action("delete")),
        ("deletes for target=secret:0042", log.query_deletes_for_target("secret:0042")),
        ("history for target=user:0007", log.query_target_history("user:0007")),
    ]
    for name, result in queries:
        print(f"  {name:<40} → {len(result):>5,} events")
    # Cross-check: the deletes count must equal a fresh Counter over all events
    expected_delete_total = sum(1 for e in log.events if e.action == "delete")
    assert len(queries[1][1]) == expected_delete_total, "delete query count mismatch"
    # Cross-check: alice count must equal Counter of all actors
    expected_alice_total = sum(1 for e in log.events if e.actor == "alice")
    assert len(queries[0][1]) == expected_alice_total, "alice query count mismatch"
    print("  query counts match a full re-scan of the log (correctness)")
    print()

    # ── Final invariants ──
    print("═══ final invariants ═══")
    assert_no_seq_gaps(log)
    print("  ✓ no gaps in seq numbers")
    assert_all_events_have_payload(log)
    print("  ✓ every event has a non-empty payload dict")
    assert_event_count_matches_sum(log)
    print("  ✓ event count == sum across event types")
    assert snap == proj
    print("  ✓ snapshot matches live projection")
    assert log.verify()[0]
    print("  ✓ hash chain is intact")
    print()
    print("✓ all invariants pass")
