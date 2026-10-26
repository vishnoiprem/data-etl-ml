# Mock 115 — E6 Meta Onsite (system-design-flavored coding)

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

## Format

- 60 minutes, 1 problem, 1 interviewer.
- Coding is the focus but the problem has system-design flavor: real-world entity, multiple data sources, throughput mentioned.

## Problem — Rate Limiter (Sliding Window)

Design a class that, given a stream of timestamps per user, allows at most `k` requests in any `w`-second window. Implement `hit(timestamp) -> bool` (True = allowed, False = rate-limited).

## Talking points

- "We need a deque of timestamps per user."
- "On hit, drop timestamps older than timestamp - w."
- "If size <= k, accept; else reject."
- "What if the user has too many hits? We should bound the deque."

## Grading rubric

- **Strong Hire**: optimal solution + discusses memory bounds, concurrency, multi-machine.
- **Hire**: correct per-user solution; briefly touches scale.
- **Lean Hire**: works but uses O(n) scan instead of deque.
- **No Hire**: doesn't get the sliding-window dequeue idea.
