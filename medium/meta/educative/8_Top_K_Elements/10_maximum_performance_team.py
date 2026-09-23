"""
MAXIMUM PERFORMANCE OF A TEAM — LeetCode 1383
=============================================
You have n engineers: engineer i has speed[i] and efficiency[i].
Pick AT MOST k engineers; the team's PERFORMANCE is:
    (sum of chosen speeds) * (min of chosen efficiencies)

Return the max performance modulo 10^9 + 7.

Two-heap pattern (the famous one)
--------------------------------
Sort engineers by efficiency DESCENDING. Sweep them one by one in that
order; the current engineer's efficiency is the MINIMUM for any team
that includes him. Keep a SPEED-heap of size ≤ k. At each step:
    • current_sum_of_speeds × current_efficiency is a candidate max.
    • If heap size == k, pop the smallest speed (the engineer who
      hurts the sum most) before deciding.

Why "min of efficiencies" works as we sweep:
    Sweeping descending guarantees everyone added after engineer i has
    efficiency ≤ i. So efficiency[i] is the team's bottleneck once i
    is in the team.

Why we evict the SLOWEST kept engineer: speed is summed positively;
the slowest one contributes least per unit.
"""

import heapq
from typing import List


def max_performance(n: int, speed: List[int], efficiency: List[int], k: int) -> int:
    MOD = 10**9 + 7
    engineers = sorted(zip(efficiency, speed), reverse=True)   # by eff desc
    speed_heap, sum_speed = [], 0
    best = 0
    for eff, sp in engineers:
        heapq.heappush(speed_heap, sp)
        sum_speed += sp
        if len(speed_heap) > k:
            sum_speed -= heapq.heappop(speed_heap)             # evict slowest
        best = max(best, sum_speed * eff)
    return best % MOD


if __name__ == "__main__":
    n, sp, ef, k = 6, [2,10,3,1,5,8], [5,4,3,9,7,6], 2
    print(max_performance(n, sp, ef, k))     # 60
