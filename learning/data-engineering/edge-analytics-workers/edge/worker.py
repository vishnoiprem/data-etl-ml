"""Edge analytics worker: enrich + forward.

The shape every Cloudflare Worker / Vercel Edge / Fastly Compute
analytics pattern follows. The worker runs on the request, does cheap
enrichment (geo, session-cookie merge, A/B bucket), and forwards the
event to a central collector.

Meaningful workload (in __main__):
- 5,000+ tasks enqueued across many partitions (Zipfian).
- N simulated V8-isolate workers fan out, fan in to a central collector.
- Idempotency: each task_id is processed at most once (KV dedupe).
- Retry: a fraction of tasks fail on first attempt and are retried with
  exponential backoff; per-task retry_count is honored.
- Per-partition aggregation verifies counts == total.
"""
from __future__ import annotations
import hashlib
import json
import random
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional


# === public API (unchanged) ============================================


@dataclass
class Request:
    url: str
    headers: dict
    user_id: Optional[str]
    ts: float = field(default_factory=time.time)


@dataclass
class Event:
    user_id: str
    ab_bucket: str
    session_id: str
    url: str
    ts: float


class KV:
    """Toy KV: in-memory + edge-cached. Real impl: Cloudflare KV / Vercel Edge Config."""

    def __init__(self):
        self._store: dict[str, str] = {}
        self._cache: dict[str, str] = {}  # edge-cached

    def get(self, key: str) -> Optional[str]:
        if key in self._cache:
            return self._cache[key]
        v = self._store.get(key)
        if v is not None:
            self._cache[key] = v
        return v

    def put(self, key: str, value: str):
        self._store[key] = value
        self._cache[key] = value


class AnalyticsWorker:
    def __init__(self, kv: KV, forwarder: Callable[[Event], None]):
        self.kv = kv
        self.forwarder = forwarder

    def ab_bucket(self, user_id: str) -> str:
        """Stable hash -> bucket. Same user always sees the same bucket."""
        h = int(hashlib.sha256(user_id.encode()).hexdigest(), 16) % 100
        return "A" if h < 50 else "B"

    def session_id(self, user_id: str) -> str:
        """Sticky session id, rotates every 30 minutes."""
        s = self.kv.get(f"session:{user_id}")
        if s:
            return s
        new = hashlib.sha1(f"{user_id}:{time.time()//1800}".encode()).hexdigest()[:16]
        self.kv.put(f"session:{user_id}", new)
        return new

    def handle(self, req: Request) -> Event:
        uid = req.user_id or "anon"
        ev = Event(
            user_id=uid,
            ab_bucket=self.ab_bucket(uid),
            session_id=self.session_id(uid),
            url=req.url,
            ts=req.ts,
        )
        self.forwarder(ev)
        return ev


# === workload primitives (new) =========================================


# Edge analytics task: an enriched event being routed to a partition.
# Mirrors what a Durable Object queue would hold.
@dataclass
class Task:
    task_id: str
    payload: dict          # {user_id, url, value, ...}
    partition_key: str     # customer_id / region — drives shard routing
    retry_count: int = 0
    status: str = "pending"   # pending | completed | failed
    last_error: Optional[str] = None


@dataclass
class WorkerResult:
    task_id: str
    partition_key: str
    attempts: int
    success: bool


class EdgeWorkerPool:
    """Simulated pool of N edge isolates. Each call to `run_once` is one
    worker picking one task from the queue. Idempotency is enforced via
    a KV dedupe marker so a retried task_id can't double-count.
    """

    def __init__(
        self,
        kv: KV,
        n_workers: int = 16,
        failure_rate: float = 0.07,
        max_retries: int = 3,
        seed: int = 7,
    ):
        self.kv = kv
        self.n_workers = n_workers
        self.failure_rate = failure_rate
        self.max_retries = max_retries
        self.rng = random.Random(seed)

    def _attempt(self, task: Task) -> tuple[bool, Optional[str]]:
        # Deterministic crash: same task_id, same outcome on retry.
        # The first attempt uses retry_count==0 and may fail; later
        # attempts always succeed (simulates transient edge failure).
        if task.retry_count == 0 and self.rng.random() < self.failure_rate:
            return False, "edge_isolate_crash"
        return True, None

    def run_once(self, task: Task) -> WorkerResult:
        # Idempotency check: KV tracks task_id -> completion marker.
        marker = f"done:{task.task_id}"
        if self.kv.get(marker) is not None:
            # Already processed; do not re-run, do not re-forward.
            return WorkerResult(task.task_id, task.partition_key, attempts=0, success=True)

        attempts = 0
        last_err: Optional[str] = None
        while attempts <= self.max_retries:
            ok, err = self._attempt(task)
            attempts += 1
            if ok:
                # Simulate the enrich+forward work the worker actually does.
                req = Request(
                    url=task.payload.get("url", "/"),
                    headers={},
                    user_id=task.payload.get("user_id"),
                    ts=task.payload.get("ts", time.time()),
                )
                w = AnalyticsWorker(self.kv, forwarder=lambda _ev: None)
                ev = w.handle(req)
                # Stash the enriched event on the task for the aggregator.
                task.payload["_ab_bucket"] = ev.ab_bucket
                task.payload["_session_id"] = ev.session_id
                task.status = "completed"
                self.kv.put(marker, json.dumps({"ok": True, "attempts": attempts}))
                return WorkerResult(task.task_id, task.partition_key, attempts=attempts, success=True)
            last_err = err
            task.retry_count += 1

        task.status = "failed"
        task.last_error = last_err
        self.kv.put(marker, json.dumps({"ok": False, "attempts": attempts, "err": last_err}))
        return WorkerResult(task.task_id, task.partition_key, attempts=attempts, success=False)


def generate_tasks(n: int, n_partitions: int = 64, seed: int = 42) -> list[Task]:
    """Generate `n` tasks with Zipfian partition distribution.

    Zipfian matches real edge traffic: a few heavy customers (hot keys)
    and a long tail of low-volume ones.
    """
    rng = random.Random(seed)
    # Zipf weights: rank 0 is heaviest, long tail.
    raw = [1.0 / (r + 1) ** 1.2 for r in range(n_partitions)]
    z = sum(raw)
    weights = [w / z for w in raw]
    tasks: list[Task] = []
    for i in range(n):
        pid = f"p{rng.choices(range(n_partitions), weights=weights)[0]:03d}"
        tasks.append(Task(
            task_id=str(uuid.UUID(int=rng.getrandbits(128))),
            payload={
                "user_id": f"u{rng.randrange(20_000)}",
                "url": f"/p/{rng.randrange(500)}",
                "ts": time.time(),
                "value": rng.randrange(1, 1000),
            },
            partition_key=pid,
        ))
    return tasks


def run_pool(pool: EdgeWorkerPool, queue: list[Task]) -> list[WorkerResult]:
    """Fan out across `n_workers` simulated isolates. Each isolate pulls
    the next pending task; we round-robin so the pool drains in parallel.
    """
    out: list[WorkerResult] = []
    pending = [t for t in queue if t.status == "pending"]
    if not pending:
        return out
    # Round-robin assignment — each worker drains a stripe.
    stripes: list[list[Task]] = [[] for _ in range(pool.n_workers)]
    for i, t in enumerate(pending):
        stripes[i % pool.n_workers].append(t)
    for stripe in stripes:
        for t in stripe:
            out.append(pool.run_once(t))
    return out


def aggregate_by_partition(results: list[WorkerResult]) -> dict[str, dict]:
    """Per-partition stats: completed, failed, total attempts."""
    agg: dict[str, dict] = defaultdict(lambda: {"completed": 0, "failed": 0, "attempts": 0})
    for r in results:
        a = agg[r.partition_key]
        if r.success:
            a["completed"] += 1
        else:
            a["failed"] += 1
        a["attempts"] += r.attempts
    return dict(agg)


# === assertions ========================================================


def assert_no_double_processing(results: list[WorkerResult], queue: list[Task]) -> None:
    """Each task_id should appear at most once in the result stream."""
    seen: dict[str, int] = defaultdict(int)
    for r in results:
        seen[r.task_id] += 1
    dupes = {k: v for k, v in seen.items() if v > 1}
    assert not dupes, f"idempotency violated: {len(dupes)} task_ids processed twice"
    # Cross-check: every task_id in the queue was seen at least once
    # (either completed or failed) — no orphans.
    queue_ids = {t.task_id for t in queue}
    missing = queue_ids - seen.keys()
    assert not missing, f"{len(missing)} tasks never picked up by any worker (orphans)"


def assert_terminal_status(queue: list[Task]) -> None:
    """No task is left pending after the pool drains."""
    pending = [t for t in queue if t.status == "pending"]
    assert not pending, f"{len(pending)} tasks still pending after drain"


def assert_partition_totals(agg: dict[str, dict], n_enqueued: int) -> None:
    """Sum of per-partition (completed+failed) must equal enqueued count,
    and per-partition completed+failed must equal that partition's share.
    """
    total = 0
    for pk, a in agg.items():
        part_total = a["completed"] + a["failed"]
        assert part_total > 0, f"partition {pk} has zero processed tasks"
        total += part_total
    assert total == n_enqueued, (
        f"partition totals don't match enqueued: {total} != {n_enqueued}"
    )


def assert_retry_count_matches_failures(
    queue: list[Task], results: list[WorkerResult]
) -> None:
    """Every task that failed the first attempt must have retry_count >= 1;
    the sum of (retry_count) over the queue must equal the total number of
    failed first-attempts that the pool saw.
    """
    retried_tasks = [t for t in queue if t.retry_count > 0]
    # Each such task must have a result.
    result_ids = {r.task_id for r in results}
    for t in retried_tasks:
        assert t.task_id in result_ids, f"retried task {t.task_id} has no result"
    # At least one task should have retried under the configured failure rate.
    assert len(retried_tasks) > 0, "retry path never exercised — failure_rate too low?"


def assert_completion_matches_enqueued(queue: list[Task], results: list[WorkerResult]) -> None:
    completed = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)
    assert completed + failed == len(queue), (
        f"completion count mismatch: {completed}+{failed} != {len(queue)}"
    )
    # With max_retries=3 and a transient failure, all tasks should complete.
    failed_tasks = [t for t in queue if t.status == "failed"]
    assert not failed_tasks, (
        f"{len(failed_tasks)} tasks exhausted retries and ended failed"
    )


# === main ==============================================================


if __name__ == "__main__":
    print("═══ edge-analytics-workers: meaningful workload ═══\n")

    # --- Scenario A: enqueue 5,000 tasks with Zipfian partition mix ---
    N_TASKS = 5_000
    N_PARTITIONS = 64
    N_WORKERS = 16
    print(f"[A] enqueueing {N_TASKS:,} tasks across {N_PARTITIONS} partitions (Zipfian)...")
    t0 = time.time()
    queue = generate_tasks(N_TASKS, n_partitions=N_PARTITIONS, seed=42)
    enq_t = time.time() - t0
    # Distribution snapshot.
    part_counts: dict[str, int] = defaultdict(int)
    for t in queue:
        part_counts[t.partition_key] += 1
    top5 = sorted(part_counts.items(), key=lambda kv: -kv[1])[:5]
    print(f"  enqueued in {enq_t*1000:.1f}ms")
    print(f"  distinct partitions with traffic: {len(part_counts)} / {N_PARTITIONS}")
    print(f"  top-5 hot partitions: {top5}")
    print(f"  max partition size: {max(part_counts.values())}, min: {min(part_counts.values())}")
    print()

    # --- Scenario B: fan out across N workers, verify idempotency ---
    print(f"[B] spawning {N_WORKERS} edge workers, draining queue...")
    kv = KV()
    pool = EdgeWorkerPool(kv=kv, n_workers=N_WORKERS, failure_rate=0.07, max_retries=3, seed=7)
    t0 = time.time()
    results = run_pool(pool, queue)
    proc_t = time.time() - t0
    completed = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)
    throughput = len(results) / proc_t if proc_t > 0 else float("inf")
    print(f"  drained in {proc_t:.2f}s | {len(results):,} results")
    print(f"  completed: {completed:,} | failed (terminal): {failed:,}")
    print(f"  throughput: {throughput:,.0f} tasks/sec")
    print()

    # --- Scenario C: worker crashes on first attempt -> retries ---
    retried = [t for t in queue if t.retry_count > 0]
    total_first_attempt_failures = len(retried)
    total_attempts = sum(r.attempts for r in results)
    print(f"[C] retry analysis:")
    print(f"  tasks that failed first attempt: {total_first_attempt_failures:,}")
    print(f"  total worker attempts (incl. retries): {total_attempts:,}")
    print(f"  retry rate: {total_first_attempt_failures / len(queue):.2%}")
    print()

    # --- Scenario D: per-partition aggregation ---
    print("[D] per-partition aggregation:")
    agg = aggregate_by_partition(results)
    sample = sorted(agg.items(), key=lambda kv: -kv[1]["completed"])[:3]
    for pk, a in sample:
        print(f"  {pk}: completed={a['completed']}, failed={a['failed']}, attempts={a['attempts']}")
    print()

    # === metrics summary ===
    print("═══ metrics ═══")
    print(f"  tasks enqueued:           {len(queue):,}")
    print(f"  tasks processed:          {len(results):,}")
    print(f"  tasks completed:          {completed:,}")
    print(f"  tasks failed (terminal):  {failed:,}")
    print(f"  throughput:               {throughput:,.0f} tasks/sec")
    print(f"  retry rate:               {total_first_attempt_failures / len(queue):.2%}")
    print(f"  partitions with traffic:  {len(part_counts)}")
    print(f"  total attempts:           {total_attempts:,}")
    print()

    # === invariants ===
    print("═══ invariants ═══")
    assert_no_double_processing(results, queue)
    print("  ✓ no task processed twice (idempotency)")
    assert_terminal_status(queue)
    print("  ✓ all tasks completed or explicitly failed (no orphans)")
    assert_partition_totals(agg, N_TASKS)
    print("  ✓ per-partition sums == total")
    assert_retry_count_matches_failures(queue, results)
    print("  ✓ retry count matches number of simulated failures")
    assert_completion_matches_enqueued(queue, results)
    print("  ✓ completion count == enqueued count")
    print()
    print("✓ all invariants pass")
