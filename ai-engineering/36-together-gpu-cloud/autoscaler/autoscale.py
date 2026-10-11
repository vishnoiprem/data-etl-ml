"""Together-style GPU cloud autoscaler: keep H100s 80%+ utilized, tail < 200ms.

The interesting engineering: a queue-depth-driven autoscaler that
fills GPUs to a target utilization while keeping tail latency under
a hard budget. The two signals (queue depth + p99 latency) need to
be combined — queue alone over-provisions, latency alone under-
provisions.

The toy captures the scheduler: a pool of GPUs, a queue, and a
controller that decides when to add or remove GPUs.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from statistics import mean


@dataclass
class GPU:
    gpu_id: int
    active: bool = True
    in_flight: int = 0
    served: int = 0
    utilization: float = 0.0


@dataclass
class Request:
    req_id: int
    tokens: int
    enqueued_at: float


class GPUScheduler:
    """Drives GPU pool size based on queue depth and observed p99 latency."""

    def __init__(self, target_utilization: float = 0.8, max_gpus: int = 16,
                 latency_budget_ms: float = 200.0, p99_window: int = 50):
        self.target_utilization = target_utilization
        self.max_gpus = max_gpus
        self.latency_budget_ms = latency_budget_ms
        self.p99_window = p99_window
        self.gpus: list[GPU] = []
        self.queue: deque[Request] = deque()
        self.latencies_ms: deque[float] = deque(maxlen=p99_window)
        self._next_req_id = 0

    def add_gpu(self) -> bool:
        if len(self.gpus) >= self.max_gpus:
            return False
        self.gpus.append(GPU(gpu_id=len(self.gpus)))
        return True

    def enqueue(self, tokens: int) -> Request:
        req = Request(req_id=self._next_req_id, tokens=tokens, enqueued_at=0.0)
        self._next_req_id += 1
        self.queue.append(req)
        return req

    def tick(self, n_completed: int = 0, latencies: list[float] | None = None) -> dict:
        """Simulate one tick: complete N requests, record latencies, scale."""
        if latencies:
            for lat in latencies:
                self.latencies_ms.append(lat)
        # compute observed metrics
        active = [g for g in self.gpus if g.active]
        util = mean([g.utilization for g in active]) if active else 0.0
        p99 = sorted(self.latencies_ms)[int(len(self.latencies_ms) * 0.99)] if self.latencies_ms else 0.0
        # decision
        action = "noop"
        if self.queue and (util > 0.9 or (p99 > self.latency_budget_ms and len(active) < self.max_gpus)):
            if self.add_gpu():
                action = "scale_up"
        elif util < 0.4 and len(active) > 1:
            self.gpus.pop()
            action = "scale_down"
        return {"n_gpus": len(self.gpus), "queue_len": len(self.queue),
                "utilization": round(util, 3), "p99_ms": round(p99, 1), "action": action}


if __name__ == "__main__":
    sched = GPUScheduler(target_utilization=0.8, max_gpus=8, latency_budget_ms=200.0)
    sched.add_gpu()  # start with 1 GPU
    # Simulate a burst: enqueue 200 requests, then drain
    for i in range(200):
        sched.enqueue(tokens=512)
    print(f"after enqueue: queue={len(sched.queue)}, gpus={len(sched.gpus)}")
    # Tick 5 times, scale up
    for t in range(5):
        s = sched.tick(n_completed=20, latencies=[180.0, 195.0, 210.0, 250.0, 175.0])
        print(f"tick {t}: {s}")
    # Then tick with low load, scale down
    for t in range(5, 10):
        s = sched.tick(n_completed=10, latencies=[120.0, 130.0, 110.0, 125.0, 115.0])
        print(f"tick {t}: {s}")
