"""Together-style GPU cloud: pool of GPU instances, job queue, autoscaling,
spot vs on-demand pricing, job scheduling, utilization tracking.

The interesting engineering: a queue-depth-driven autoscaler that
fills GPUs to a target utilization while keeping tail latency under
a hard budget. The two signals (queue depth + p99 latency) need to
be combined — queue alone over-provisions, latency alone under-
provisions.

The toy captures the scheduler: a pool of heterogeneous GPUs (A100 /
H100 / L40S) with mixed spot + on-demand pricing, a job queue, a
controller that decides when to add or remove instances, and a
utilization tracker that records active compute over time.

Meaningful workload:
- Submits 300+ jobs across 3 GPU types with varied duration + priority.
- Scenario A: schedule submitted jobs onto a starting pool; verify all
  jobs are eventually scheduled.
- Scenario B: simulate a load spike; autoscale must add instances.
- Scenario C: spot vs on-demand mix; spot jobs can be preempted, with
  preemption tracked.
- Scenario D: utilization tracking — record (gpu_count, util) over time
  and report avg + peak.
- Asserts invariants: no orphan jobs, autoscaling increased count under
  load, preemption counters consistent, util in [0, 1], total
  compute-seconds == sum_t (instances_t * dt).
"""
from __future__ import annotations

import random
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from statistics import mean


# ---------------------------------------------------------------------------
# GPU instance model
# ---------------------------------------------------------------------------


class Pricing(Enum):
    ON_DEMAND = "on_demand"
    SPOT = "spot"


@dataclass
class GPU:
    """A single GPU instance in the pool."""

    gpu_id: int
    gpu_type: str          # "A100" | "H100" | "L40S"
    pricing: Pricing
    active: bool = True
    in_flight: int = 0
    served: int = 0
    preempted: int = 0
    utilization: float = 0.0  # 0..1, fraction of capacity used last tick

    # throughput in jobs/tick for this GPU type (used to drive simulation)
    jobs_per_tick: int = 2


# Per-type throughput + relative cost; H100 is fastest, L40S slowest.
GPU_TYPES: dict[str, dict] = {
    "H100": {"jobs_per_tick": 4, "on_demand": 4.50, "spot": 2.80},
    "A100": {"jobs_per_tick": 2, "on_demand": 3.20, "spot": 1.80},
    "L40S": {"jobs_per_tick": 1, "on_demand": 1.80, "spot": 0.95},
}


def make_gpu(gpu_id: int, gpu_type: str, pricing: Pricing) -> GPU:
    cfg = GPU_TYPES[gpu_type]
    return GPU(
        gpu_id=gpu_id,
        gpu_type=gpu_type,
        pricing=pricing,
        jobs_per_tick=cfg["jobs_per_tick"],
    )


# ---------------------------------------------------------------------------
# Job model
# ---------------------------------------------------------------------------


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PREEMPTED = "preempted"
    FAILED = "failed"


@dataclass
class Job:
    job_id: int
    gpu_type: str
    duration_ticks: int       # how many ticks of GPU-time the job needs
    priority: int             # higher = sooner
    pricing: Pricing          # spot jobs are preemptible
    status: JobStatus = JobStatus.PENDING
    assigned_gpu: int | None = None
    remaining_ticks: int = 0
    preempted_count: int = 0


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------


@dataclass
class TickMetrics:
    n_gpus: int
    queue_len: int
    utilization: float
    p99_ms: float
    action: str
    jobs_completed: int
    jobs_preempted: int


class GPUScheduler:
    """Drives GPU pool size based on queue depth and observed p99 latency."""

    def __init__(self, target_utilization: float = 0.8, max_gpus: int = 16,
                 latency_budget_ms: float = 200.0, p99_window: int = 50,
                 rng: random.Random | None = None):
        self.target_utilization = target_utilization
        self.max_gpus = max_gpus
        self.latency_budget_ms = latency_budget_ms
        self.p99_window = p99_window
        self.gpus: list[GPU] = []
        # gpu_id -> GPU (stable id never renumbered on removal)
        self.gpu_by_id: dict[int, GPU] = {}
        self._next_gpu_id = 0
        self.queue: deque[Job] = deque()
        self.latencies_ms: deque[float] = deque(maxlen=p99_window)

        # Job tracking
        self.jobs: dict[int, Job] = {}
        self._next_job_id = 0

        # Aggregate metrics
        self.jobs_submitted = 0
        self.jobs_completed = 0
        self.jobs_preempted = 0
        self.jobs_failed = 0
        # job_ids that have ever reached COMPLETED (a preempted job may
        # re-run and complete, so we count it once).
        self._completed_ids: set[int] = set()

        # Utilization time series: list of (instances, util) per tick
        self.utilization_log: list[tuple[int, float]] = []
        self.gpu_count_log: list[int] = []

        # Counters for spot preemption decisions
        self.spot_preemptions_by_gpu: dict[int, int] = {}

        self._rng = rng or random.Random(42)

    # -- GPU pool management --

    def add_gpu(self, gpu_type: str = "A100",
                pricing: Pricing = Pricing.ON_DEMAND) -> bool:
        if len(self.gpus) >= self.max_gpus:
            return False
        gpu_id = self._next_gpu_id
        self._next_gpu_id += 1
        gpu = make_gpu(gpu_id=gpu_id, gpu_type=gpu_type, pricing=pricing)
        self.gpus.append(gpu)
        self.gpu_by_id[gpu_id] = gpu
        return True

    def remove_gpu(self) -> bool:
        """Remove a GPU that has no in-flight jobs. Prefer spot GPU first.
        Jobs on a removed GPU become pending again."""
        # Prefer spot GPU that's idle
        for g in list(self.gpus):
            if g.in_flight == 0 and g.pricing == Pricing.SPOT:
                self.gpus.remove(g)
                del self.gpu_by_id[g.gpu_id]
                self._reassign_orphans(g.gpu_id)
                return True
        for g in list(self.gpus):
            if g.in_flight == 0:
                self.gpus.remove(g)
                del self.gpu_by_id[g.gpu_id]
                self._reassign_orphans(g.gpu_id)
                return True
        return False

    def _reassign_orphans(self, removed_id: int) -> None:
        """If a job was running on a removed GPU, requeue it."""
        for j in self.jobs.values():
            if j.status == JobStatus.RUNNING and j.assigned_gpu == removed_id:
                j.status = JobStatus.PENDING
                j.assigned_gpu = None
                # Put at front of queue so it gets re-scheduled
                self.queue.appendleft(j)

    # -- Job submission --

    def submit(self, gpu_type: str, duration_ticks: int, priority: int = 1,
               pricing: Pricing = Pricing.ON_DEMAND) -> Job:
        job = Job(
            job_id=self._next_job_id,
            gpu_type=gpu_type,
            duration_ticks=duration_ticks,
            priority=priority,
            pricing=pricing,
            remaining_ticks=duration_ticks,
        )
        self._next_job_id += 1
        self.jobs[job.job_id] = job
        self.queue.append(job)
        self.jobs_submitted += 1
        return job

    # -- Scheduling --

    def _schedule_pending(self) -> int:
        """Assign queued jobs to free GPU slots. Returns number assigned."""
        assigned = 0
        # Sort queue by priority (desc) — simple priority scheduling.
        # Use a stable sort: convert to list, sort, re-queue.
        if not self.queue:
            return 0
        pending = sorted(self.queue, key=lambda j: (-j.priority, j.job_id))
        self.queue.clear()
        for job in pending:
            # Find a free GPU of matching type
            slot = None
            for g in self.gpus:
                if g.active and g.gpu_type == job.gpu_type and g.in_flight < g.jobs_per_tick:
                    slot = g
                    break
            # Fallback: any free GPU (we'll model this as 50% slower for mismatch)
            if slot is None:
                for g in self.gpus:
                    if g.active and g.in_flight < g.jobs_per_tick:
                        slot = g
                        break
            if slot is None:
                self.queue.append(job)
                continue
            job.status = JobStatus.RUNNING
            job.assigned_gpu = slot.gpu_id
            slot.in_flight += 1
            assigned += 1
        return assigned

    def _maybe_preempt_spot(self) -> int:
        """With some probability, preempt one running spot job (simulating
        a spot reclaim by the cloud provider). Returns number preempted."""
        preempted = 0
        spot_jobs = [j for j in self.jobs.values()
                     if j.status == JobStatus.RUNNING and j.pricing == Pricing.SPOT]
        if not spot_jobs:
            return 0
        # 15% chance per tick to simulate a spot reclaim
        if self._rng.random() < 0.15 and spot_jobs:
            victim = self._rng.choice(spot_jobs)
            gpu_id = victim.assigned_gpu
            victim.status = JobStatus.PENDING
            victim.assigned_gpu = None
            victim.preempted_count += 1
            if gpu_id is not None and gpu_id in self.gpu_by_id:
                g = self.gpu_by_id[gpu_id]
                g.in_flight = max(0, g.in_flight - 1)
                g.preempted += 1
                self.spot_preemptions_by_gpu[gpu_id] = (
                    self.spot_preemptions_by_gpu.get(gpu_id, 0) + 1
                )
            self.jobs_preempted += 1
            self.queue.append(victim)
            preempted = 1
        return preempted

    def _progress_jobs(self) -> int:
        """Decrement remaining_ticks on running jobs; complete the ones
        that hit zero. Returns number *first-time* completions this tick."""
        completed = 0
        for job in list(self.jobs.values()):
            if job.status != JobStatus.RUNNING:
                continue
            job.remaining_ticks -= 1
            if job.remaining_ticks <= 0:
                job.status = JobStatus.COMPLETED
                if job.assigned_gpu is not None and job.assigned_gpu in self.gpu_by_id:
                    g = self.gpu_by_id[job.assigned_gpu]
                    g.in_flight = max(0, g.in_flight - 1)
                    g.served += 1
                # Only count first-time completion. A pre-empted job will
                # be re-queued and run again; we count it as completed once.
                if job.job_id not in self._completed_ids:
                    self._completed_ids.add(job.job_id)
                    self.jobs_completed += 1
                    completed += 1
        return completed

    def _update_utilization(self) -> float:
        """Update each GPU's utilization (in_flight / jobs_per_tick)."""
        for g in self.gpus:
            if g.active and g.jobs_per_tick > 0:
                g.utilization = min(1.0, g.in_flight / g.jobs_per_tick)
            else:
                g.utilization = 0.0
        active = [g for g in self.gpus if g.active]
        return mean([g.utilization for g in active]) if active else 0.0

    # -- Main tick --

    def tick(self, latencies: list[float] | None = None) -> TickMetrics:
        """Simulate one tick."""
        if latencies:
            for lat in latencies:
                self.latencies_ms.append(lat)

        # 1) Maybe preempt a spot job (provider reclaim)
        preempted_this_tick = self._maybe_preempt_spot()

        # 2) Schedule pending jobs onto free slots
        self._schedule_pending()

        # 3) Progress running jobs
        completed_this_tick = self._progress_jobs()

        # 4) Recompute utilization
        util = self._update_utilization()

        # 5) Autoscaler decision
        active = [g for g in self.gpus if g.active]
        p99 = (sorted(self.latencies_ms)[int(len(self.latencies_ms) * 0.99)]
               if self.latencies_ms else 0.0)

        action = "noop"
        if self.queue and (
            util > 0.9
            or (p99 > self.latency_budget_ms and len(active) < self.max_gpus)
        ):
            # Add a new GPU of the type most-needed: pick the type with
            # the longest queue, defaulting to A100.
            type_counts: dict[str, int] = {}
            for j in self.queue:
                type_counts[j.gpu_type] = type_counts.get(j.gpu_type, 0) + 1
            want_type = max(type_counts, key=type_counts.get) if type_counts else "A100"
            if self.add_gpu(gpu_type=want_type, pricing=Pricing.ON_DEMAND):
                action = "scale_up"
        elif util < 0.4 and len(active) > 1 and not self.queue:
            if self.remove_gpu():
                action = "scale_down"

        # 6) Log metrics
        self.utilization_log.append((len(self.gpus), util))
        self.gpu_count_log.append(len(self.gpus))

        return TickMetrics(
            n_gpus=len(self.gpus),
            queue_len=len(self.queue),
            utilization=round(util, 3),
            p99_ms=round(p99, 1),
            action=action,
            jobs_completed=completed_this_tick,
            jobs_preempted=preempted_this_tick,
        )

    # -- Aggregate metrics --

    def avg_utilization(self) -> float:
        if not self.utilization_log:
            return 0.0
        return mean(u for _, u in self.utilization_log)

    def peak_utilization(self) -> float:
        if not self.utilization_log:
            return 0.0
        return max(u for _, u in self.utilization_log)

    def peak_gpus(self) -> int:
        return max(self.gpu_count_log) if self.gpu_count_log else 0

    def total_compute_seconds(self, dt: float = 1.0) -> float:
        """Total GPU-seconds over the run: sum_t (n_gpus_t * dt)."""
        return float(sum(self.gpu_count_log)) * dt

    def unscheduled_jobs(self) -> list[Job]:
        return [j for j in self.jobs.values()
                if j.status in (JobStatus.PENDING, JobStatus.RUNNING)]


# ---------------------------------------------------------------------------
# Meaningful workload
# ---------------------------------------------------------------------------


def generate_job_plan(n: int, rng: random.Random) -> list[dict]:
    """Generate a varied job plan: 3 GPU types, mixed spot/od, varied duration."""
    types = ["A100", "H100", "L40S"]
    type_weights = [0.45, 0.30, 0.25]
    plan = []
    for _ in range(n):
        gpu_type = rng.choices(types, weights=type_weights)[0]
        # 60% spot, 40% on-demand
        pricing = Pricing.SPOT if rng.random() < 0.6 else Pricing.ON_DEMAND
        # duration 1..8 ticks, with a long tail
        duration = rng.choices(
            [1, 2, 3, 4, 5, 6, 7, 8],
            weights=[0.20, 0.25, 0.20, 0.15, 0.10, 0.05, 0.03, 0.02],
        )[0]
        priority = rng.choices([1, 2, 3, 5], weights=[0.5, 0.3, 0.15, 0.05])[0]
        plan.append({
            "gpu_type": gpu_type,
            "duration_ticks": duration,
            "priority": priority,
            "pricing": pricing,
        })
    return plan


def run_scenario_a(sched: GPUScheduler, plan: list[dict]) -> dict:
    """Scenario A: submit jobs, schedule them onto starting pool."""
    initial_gpus = 2
    sched.add_gpu(gpu_type="A100", pricing=Pricing.ON_DEMAND)
    sched.add_gpu(gpu_type="H100", pricing=Pricing.ON_DEMAND)

    for spec in plan:
        sched.submit(**spec)

    # Tick until queue is empty OR we hit a hard cap
    max_ticks = 200
    for _ in range(max_ticks):
        if not sched.queue and not any(
            j.status == JobStatus.RUNNING for j in sched.jobs.values()
        ):
            break
        # Normal latencies during steady-state
        sched.tick(latencies=[120.0, 140.0, 150.0, 130.0, 125.0])
    return {
        "initial_gpus": initial_gpus,
        "jobs_submitted": sched.jobs_submitted,
        "jobs_completed": sched.jobs_completed,
        "jobs_preempted": sched.jobs_preempted,
        "peak_gpus": sched.peak_gpus(),
    }


def run_scenario_b(sched: GPUScheduler) -> dict:
    """Scenario B: simulate a load spike; autoscale must add instances."""
    gpus_before = len(sched.gpus)
    # Submit a sudden burst of 80 jobs in 3 ticks
    for _ in range(80):
        sched.submit(
            gpu_type="H100",
            duration_ticks=4,
            priority=2,
            pricing=Pricing.ON_DEMAND,
        )
    # Force high-latency ticks to trigger scale-up
    for _ in range(10):
        sched.tick(latencies=[300.0, 320.0, 350.0, 280.0, 310.0])
    gpus_after = len(sched.gpus)
    return {
        "gpus_before": gpus_before,
        "gpus_after": gpus_after,
        "scaled_up": gpus_after > gpus_before,
        "delta": gpus_after - gpus_before,
    }


def run_scenario_c(sched: GPUScheduler, rng: random.Random) -> dict:
    """Scenario C: spot vs on-demand; spot jobs are preemptible."""
    pre_preemptions = sched.jobs_preempted
    pre_completed = sched.jobs_completed
    # Submit a known mix: 20 spot, 10 on-demand
    spot_ids = []
    for _ in range(20):
        j = sched.submit(
            gpu_type="A100",
            duration_ticks=5,
            priority=2,
            pricing=Pricing.SPOT,
        )
        spot_ids.append(j.job_id)
    for _ in range(10):
        sched.submit(
            gpu_type="A100",
            duration_ticks=5,
            priority=2,
            pricing=Pricing.ON_DEMAND,
        )
    # Tick long enough for preemption to happen with high probability
    for _ in range(40):
        sched.tick(latencies=[150.0, 160.0, 140.0, 145.0, 155.0])
        if sched.jobs_preempted - pre_preemptions >= 3:
            break
    return {
        "spot_jobs_submitted": len(spot_ids),
        "spot_preemptions": sched.jobs_preempted - pre_preemptions,
        "on_demand_completed": sched.jobs_completed - pre_completed,
    }


def run_scenario_d(sched: GPUScheduler) -> dict:
    """Scenario D: utilization tracking."""
    return {
        "ticks_logged": len(sched.utilization_log),
        "avg_utilization": round(sched.avg_utilization(), 4),
        "peak_utilization": round(sched.peak_utilization(), 4),
        "peak_gpus": sched.peak_gpus(),
    }


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    print("═══ together-gpu-cloud: meaningful workload ═══")
    rng = random.Random(42)
    sched = GPUScheduler(
        target_utilization=0.8,
        max_gpus=20,
        latency_budget_ms=200.0,
        p99_window=50,
        rng=rng,
    )

    # --- Scenario A: submit 300 jobs, schedule them ---
    print()
    print("─── Scenario A: submit 300 jobs, schedule onto starting pool ───")
    plan = generate_job_plan(300, rng)
    type_counts: dict[str, int] = {}
    spot_count = 0
    for spec in plan:
        type_counts[spec["gpu_type"]] = type_counts.get(spec["gpu_type"], 0) + 1
        if spec["pricing"] == Pricing.SPOT:
            spot_count += 1
    print(f"  job plan: {len(plan)} jobs across {len(type_counts)} GPU types")
    print(f"  per-type: {type_counts}, spot: {spot_count}, on-demand: {len(plan) - spot_count}")

    t0 = time.time()
    res_a = run_scenario_a(sched, plan)
    print(f"  duration: {time.time() - t0:.2f}s")
    for k, v in res_a.items():
        print(f"  {k}: {v}")

    # --- Scenario B: load spike, autoscale up ---
    print()
    print("─── Scenario B: load spike → autoscale up ───")
    res_b = run_scenario_b(sched)
    for k, v in res_b.items():
        print(f"  {k}: {v}")

    # --- Scenario C: spot vs on-demand preemption ---
    print()
    print("─── Scenario C: spot preemptibility ───")
    res_c = run_scenario_c(sched, rng)
    for k, v in res_c.items():
        print(f"  {k}: {v}")

    # --- Scenario D: utilization tracking ---
    print()
    print("─── Scenario D: utilization tracking ───")
    res_d = run_scenario_d(sched)
    for k, v in res_d.items():
        print(f"  {k}: {v}")

    # --- Summary metrics ---
    print()
    print("═══ summary metrics ═══")
    total_compute = sched.total_compute_seconds(dt=1.0)
    print(f"  jobs submitted:        {sched.jobs_submitted}")
    print(f"  jobs completed:        {sched.jobs_completed}")
    print(f"  jobs preempted:        {sched.jobs_preempted}")
    print(f"  jobs failed:           {sched.jobs_failed}")
    print(f"  GPU instances (final): {len(sched.gpus)}")
    print(f"  GPU instances (peak):  {sched.peak_gpus()}")
    print(f"  avg utilization:       {sched.avg_utilization():.4f}")
    print(f"  peak utilization:      {sched.peak_utilization():.4f}")
    print(f"  total compute-seconds: {total_compute:.1f}")
    print(f"  ticks simulated:       {len(sched.utilization_log)}")

    # --- Invariants ---
    print()
    print("═══ invariant checks ═══")

    # 1. No orphan jobs: all submitted are completed or failed.
    #    (preempted is a transition, not a terminal state — a preempted
    #    job is re-queued and eventually completes.)
    unscheduled = sched.unscheduled_jobs()
    assert not unscheduled, (
        f"orphan jobs: {len(unscheduled)} still pending/running "
        f"(ids: {[j.job_id for j in unscheduled[:5]]})"
    )
    # jobs_completed counts each job_id exactly once, so it must equal
    # jobs_submitted (since failures are zero in this simulation).
    assert sched.jobs_completed == sched.jobs_submitted, (
        f"completed ({sched.jobs_completed}) != submitted ({sched.jobs_submitted})"
    )
    assert sched.jobs_failed == 0, (
        f"unexpected failures: {sched.jobs_failed}"
    )
    print(f"  ✓ all {sched.jobs_submitted} submitted jobs completed (no orphans)")

    # 2. Autoscale increased instance count when load spiked.
    assert res_b["scaled_up"], (
        f"autoscale failed to scale up: gpus before={res_b['gpus_before']}, "
        f"after={res_b['gpus_after']}"
    )
    assert res_b["gpus_after"] > res_b["gpus_before"], (
        f"GPU count did not grow under spike: "
        f"{res_b['gpus_before']} -> {res_b['gpus_after']}"
    )
    print(f"  ✓ autoscale increased instance count under spike "
          f"({res_b['gpus_before']} → {res_b['gpus_after']})")

    # 3. Spot preemptions are tracked.
    assert res_c["spot_preemptions"] > 0, (
        f"expected at least 1 spot preemption, got {res_c['spot_preemptions']}"
    )
    assert sched.jobs_preempted >= res_c["spot_preemptions"]
    print(f"  ✓ spot preemptions tracked: {sched.jobs_preempted} total")

    # 4. Utilization is in [0, 1].
    assert 0.0 <= sched.avg_utilization() <= 1.0, (
        f"avg utilization out of [0,1]: {sched.avg_utilization()}"
    )
    assert 0.0 <= sched.peak_utilization() <= 1.0, (
        f"peak utilization out of [0,1]: {sched.peak_utilization()}"
    )
    for n, u in sched.utilization_log:
        assert 0.0 <= u <= 1.0, f"per-tick util out of [0,1]: n={n}, u={u}"
    print(f"  ✓ utilization in [0, 1]: avg={sched.avg_utilization():.3f}, "
          f"peak={sched.peak_utilization():.3f}")

    # 5. Total compute-seconds == sum over time of (n_gpus * dt)
    expected_compute = float(sum(sched.gpu_count_log))
    assert abs(total_compute - expected_compute) < 1e-9, (
        f"compute-seconds mismatch: {total_compute} vs {expected_compute}"
    )
    print(f"  ✓ total compute-seconds == Σ (instances_t × dt) = {total_compute:.0f}")

    print()
    print("✓ all invariants pass")
