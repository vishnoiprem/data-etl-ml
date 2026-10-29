"""
Cell 05 (full-loop): Token Bucket Rate Limiter

The Round 2.4 coding answer. The rate limiter is asked 1/3 times
in L6 DE interviews. Token bucket: refills at rate, capacity caps burst.
"""
import time
from threading import Lock

class RateLimiter:
    """
    Token bucket rate limiter.

    - rate_per_sec: sustained refill rate
    - capacity: max burst size
    - try_acquire(n): non-blocking, returns True if got n tokens
    """
    def __init__(self, rate_per_sec, capacity):
        self.rate = rate_per_sec
        self.capacity = capacity
        self.tokens = capacity  # start full (allow immediate burst)
        self.last = time.monotonic()
        self.lock = Lock()
        self.total_acquired = 0
        self.total_rejected = 0

    def try_acquire(self, n=1):
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last = now
            if self.tokens >= n:
                self.tokens -= n
                self.total_acquired += n
                return True
            self.total_rejected += n
            return False

    def wait_ms(self):
        """How long until n tokens are available?"""
        with self.lock:
            if self.tokens >= 1:
                return 0
            return (1 - self.tokens) / self.rate * 1000


# Demo: OpenAI tier limits
# Tier 4: 30k RPM, burst 5k. For our app: 3500 RPM, capacity 5000.
print("=" * 60)
print("DEMO: rate limiter for OpenAI embedding API")
print("=" * 60)
print("Config: rate=3500/min = 58.3/sec, capacity=5000 (burst)")

limiter = RateLimiter(rate_per_sec=58.3, capacity=5000)

# Burst: 5000 immediate acquires should succeed (capacity allows it)
burst_ok = 0
for _ in range(5000):
    if limiter.try_acquire():
        burst_ok += 1
print(f"\nBurst test (5000 immediate): {burst_ok} succeeded (cap=5000, OK)")

# Now limiter should be empty; next 100 should mostly fail
time.sleep(0.1)  # 0.1s = ~5.8 tokens refilled
after_wait_ok = 0
for _ in range(100):
    if limiter.try_acquire():
        after_wait_ok += 1
print(f"After 0.1s wait, 100 acquires: {after_wait_ok} succeeded (~5.8 refilled + ~0 leftover)")

# Sustained: 58 per second for 5 seconds
print("\n" + "=" * 60)
print("Sustained: 58 acquires/sec for 5 sec")
print("=" * 60)
sustained_ok = 0
sustained_fail = 0
for sec in range(5):
    sec_ok = 0
    for _ in range(58):
        if limiter.try_acquire():
            sec_ok += 1
    sustained_ok += sec_ok
    time.sleep(1.0)
print(f"  Acquired: {sustained_ok}/290 ({100*sustained_ok/290:.0f}%)")
print(f"  Rejected: {sustained_fail}")
print(f"  Total: {limiter.total_acquired:,} acquired, {limiter.total_rejected:,} rejected")

# Multi-key (per-user fairness)
print("\n" + "=" * 60)
print("EXTENSION: per-user fairness (the L6 follow-up)")
print("=" * 60)
print("""
Naive: one global limiter. One user spamming -> everyone blocked.

Better: per-user limiter + global limiter (two-tier).
  - Per-user: 60 RPM, cap 100 (prevents one user from starving others)
  - Global: 3500 RPM, cap 5000 (enforces OpenAI tier)
  - try_acquire(user_id):
      if not per_user[user_id].try_acquire(): return False
      if not global.try_acquire():
          per_user[user_id].release()  # rollback
          return False
      return True

This is what the production code looks like. Token bucket per user
prevents the 'one user DOSes the system' failure mode.
""")
