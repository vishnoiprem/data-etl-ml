"""
Per-second GPU-time accumulator for a Cog-style inference API.

Real billing is a function of (gpu_type, seconds_occupied, region).
This module computes that, with a usage log and a per-tenant aggregator
so the bill actually matches the work.
"""
from __future__ import annotations
import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class GPUPriceCard:
    """The $/sec you pay per GPU, per region. Real impl pulls from a price API."""
    a10g_us_east: float = 0.000222      # $0.80/hr / 3600s
    h100_us_east: float = 0.001028      # $3.70/hr / 3600s
    t4_us_east: float = 0.000139       # $0.50/hr / 3600s


@dataclass
class UsageEvent:
    request_id: str
    tenant: str
    gpu_type: str
    seconds: float
    ts: float = field(default_factory=time.time)


class Bill:
    def __init__(self, prices: GPUPriceCard | None = None):
        self.prices = prices or GPUPriceCard()
        self.events: list[UsageEvent] = []
        self._per_tenant: dict[str, list[UsageEvent]] = defaultdict(list)

    def record(self, request_id: str, tenant: str, gpu_type: str, seconds: float):
        ev = UsageEvent(request_id=request_id, tenant=tenant, gpu_type=gpu_type, seconds=seconds)
        self.events.append(ev)
        self._per_tenant[tenant].append(ev)

    def tenant_total(self, tenant: str) -> float:
        total = 0.0
        for ev in self._per_tenant[tenant]:
            rate = getattr(self.prices, f"{ev.gpu_type}_us_east", 0.0)
            total += ev.seconds * rate
        return round(total, 6)

    def summary(self) -> dict:
        return {
            tenant: {
                "requests": len(evs),
                "total_seconds": round(sum(e.seconds for e in evs), 3),
                "bill_usd": self.tenant_total(tenant),
            }
            for tenant, evs in self._per_tenant.items()
        }


# --- Reference usage --------------------------------------------------------

if __name__ == "__main__":
    bill = Bill()

    # tenant "acme" runs 100 sdxl predictions, 2.5s each, on A10G
    for i in range(100):
        bill.record(request_id=f"req-{i}", tenant="acme", gpu_type="a10g", seconds=2.5)
    # tenant "globex" runs 5 large model predictions, 18s each, on H100
    for i in range(5):
        bill.record(request_id=f"g-{i}", tenant="globex", gpu_type="h100", seconds=18.0)

    for tenant, summary in bill.summary().items():
        print(f"{tenant}: {summary['requests']} reqs, ${summary['bill_usd']}")
