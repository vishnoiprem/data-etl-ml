"""Mock 115 — E6 Meta onsite: per-user rate limiter with a sliding window."""

from collections import defaultdict, deque


class RateLimiter:
    """Allow at most ``limit`` hits per user in any ``window_seconds`` window.

    hit(timestamp) returns True if allowed, False if rate-limited.
    """

    def __init__(self, limit, window_seconds):
        self.limit = limit
        self.window = window_seconds
        self.hits = defaultdict(deque)  # user_id -> deque of recent timestamps

    def hit(self, user_id, timestamp):
        q = self.hits[user_id]
        # Drop timestamps that fell out of the window.
        while q and q[0] <= timestamp - self.window:
            q.popleft()
        if len(q) < self.limit:
            q.append(timestamp)
            return True
        return False


if __name__ == "__main__":
    rl = RateLimiter(limit=3, window_seconds=10)
    print(rl.hit("u1", 1))    # True
    print(rl.hit("u1", 2))    # True
    print(rl.hit("u1", 3))    # True
    print(rl.hit("u1", 4))    # False — 3 in [1..4] excluding 0..-6, but limit is 3, so 4th rejected
    print(rl.hit("u1", 12))   # True — 1, 2, 3 are now out of window
