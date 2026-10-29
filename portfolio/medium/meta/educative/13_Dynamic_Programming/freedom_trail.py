"""
Freedom Trail - 20 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/freedom-trail

Given a circular ring (string) and a keyword, find min steps to spell the keyword.
Each rotation = 1 step, each button press = 1 step.

KEY INSIGHT:
DP over (i, j) where i = position in key, j = current position in ring.
dp[i][j] = min steps to spell key[i:] starting at ring position j.
Recurrence: dp[i][j] = min over k (ring[k] == key[i]) of
  abs(j - k) rotation steps + dp[i+1][k] + 1 press.

Base: dp[len(key)][j] = 0.

Examples:
    ring="godding", key="gd" -> 4
    ring="godding", key="godding" -> 13

Constraints:
- 1 <= ring.length, key.length <= 100
- Lowercase English letters.
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: 2D DP (BEST - Memorize!)
# ============================================================
def findRotateSteps_1(ring, key):
    n = len(ring)
    m = len(key)

    # Build map: char -> list of positions in ring
    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    # dp[i][j] = min steps to spell key[i:] when ring is at position j
    INF = float('inf')
    dp = [[INF] * n for _ in range(m + 1)]
    # Base: empty key
    for j in range(n):
        dp[m][j] = 0

    # Fill from end to start
    for i in range(m - 1, -1, -1):
        target_char = key[i]
        for j in range(n):
            # Try each position k in ring with char == target_char
            best = INF
            for k in char_positions[target_char]:
                # rotation steps = min(|j - k|, n - |j - k|)
                diff = abs(j - k)
                rot = min(diff, n - diff)
                best = min(best, rot + dp[i + 1][k] + 1)  # +1 for press
            dp[i][j] = best

    return dp[0][0]


# ============================================================
# Way 2: Memoized recursion
# ============================================================
def findRotateSteps_2(ring, key):
    n = len(ring)
    m = len(key)
    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    memo = {}

    def helper(i, j):
        # i = position in key, j = current position in ring
        if i == m:
            return 0
        if (i, j) in memo:
            return memo[(i, j)]
        best = float('inf')
        for k in char_positions[key[i]]:
            diff = abs(j - k)
            rot = min(diff, n - diff)
            best = min(best, rot + helper(i + 1, k) + 1)
        memo[(i, j)] = best
        return best

    return helper(0, 0)


# ============================================================
# Way 3: DP with 1D array (rolling)
# ============================================================
def findRotateSteps_3(ring, key):
    n = len(ring)
    m = len(key)
    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    INF = float('inf')
    # dp[j] = min steps to spell key from current position onwards, starting at ring[j]
    dp = [0] * n  # base: empty key

    for i in range(m - 1, -1, -1):
        new_dp = [INF] * n
        target = key[i]
        for j in range(n):
            for k in char_positions[target]:
                diff = abs(j - k)
                rot = min(diff, n - diff)
                new_dp[j] = min(new_dp[j], rot + dp[k] + 1)
        dp = new_dp

    return dp[0]


# ============================================================
# Way 4: Brute force recursion (no memo)
# ============================================================
def findRotateSteps_4(ring, key):
    n = len(ring)
    m = len(key)
    if m == 0:
        return 0

    def helper(i, j):
        if i == m:
            return 0
        best = float('inf')
        for k in range(n):
            if ring[k] == key[i]:
                diff = abs(j - k)
                rot = min(diff, n - diff)
                best = min(best, rot + helper(i + 1, k) + 1)
        return best

    return helper(0, 0)


# ============================================================
# Way 5: lru_cache
# ============================================================
from functools import lru_cache


def findRotateSteps_5(ring, key):
    n = len(ring)
    m = len(key)

    @lru_cache(maxsize=None)
    def helper(i, j):
        if i == m:
            return 0
        best = float('inf')
        for k in range(n):
            if ring[k] == key[i]:
                diff = abs(j - k)
                rot = min(diff, n - diff)
                best = min(best, rot + helper(i + 1, k) + 1)
        return best

    return helper(0, 0)


# ============================================================
# Way 6: Class-based
# ============================================================
class FreedomTrail_6:
    def __init__(self, ring, key):
        self.ring = ring
        self.key = key

    def compute(self):
        n = len(self.ring)
        m = len(self.key)
        from collections import defaultdict
        self.char_positions = defaultdict(list)
        for i, c in enumerate(self.ring):
            self.char_positions[c].append(i)

        self.memo = {}

        def helper(i, j):
            if i == m:
                return 0
            if (i, j) in self.memo:
                return self.memo[(i, j)]
            best = float('inf')
            for k in self.char_positions[self.key[i]]:
                diff = abs(j - k)
                rot = min(diff, n - diff)
                best = min(best, rot + helper(i + 1, k) + 1)
            self.memo[(i, j)] = best
            return best

        return helper(0, 0)


def findRotateSteps_6(ring, key):
    return FreedomTrail_6(ring, key).compute()


# ============================================================
# Way 7: numpy vectorized (simplified)
# ============================================================
def findRotateSteps_7(ring, key):
    import numpy as np
    n = len(ring)
    m = len(key)
    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    INF = float('inf')
    dp = np.zeros(n, dtype=np.int64)
    for i in range(m - 1, -1, -1):
        new_dp = np.full(n, INF, dtype=np.int64)
        target = key[i]
        for j in range(n):
            for k in char_positions[target]:
                diff = abs(j - k)
                rot = min(diff, n - diff)
                val = rot + int(dp[k]) + 1
                if val < new_dp[j]:
                    new_dp[j] = val
        dp = new_dp
    return int(dp[0])


# ============================================================
# Way 8: BFS over states
# ============================================================
def findRotateSteps_8(ring, key):
    n = len(ring)
    m = len(key)
    if m == 0:
        return 0

    from collections import defaultdict, deque
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    # BFS: state = (position in key, ring position)
    # Each step: rotate to match char + press
    # We can BFS layer by layer
    # Actually use Dijkstra since costs vary

    import heapq
    heap = [(0, 0, 0)]  # (steps, key_pos, ring_pos)
    visited = {}

    while heap:
        steps, ki, rp = heapq.heappop(heap)
        if ki == m:
            return steps
        if (ki, rp) in visited:
            continue
        visited[(ki, rp)] = steps

        for k in char_positions[key[ki]]:
            diff = abs(rp - k)
            rot = min(diff, n - diff)
            heapq.heappush(heap, (steps + rot + 1, ki + 1, k))

    return -1


# ============================================================
# Way 9: DP with min helper
# ============================================================
def findRotateSteps_9(ring, key):
    n = len(ring)
    m = len(key)
    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    INF = float('inf')
    dp = [0] * n

    def compute_rot(j, k):
        diff = abs(j - k)
        return min(diff, n - diff)

    for i in range(m - 1, -1, -1):
        new_dp = [INF] * n
        target = key[i]
        for j in range(n):
            new_dp[j] = min(compute_rot(j, k) + dp[k] + 1 for k in char_positions[target])
        dp = new_dp

    return dp[0]


# ============================================================
# Way 10: Helper functions
# ============================================================
def findRotateSteps_10(ring, key):
    n = len(ring)
    m = len(key)

    def rotation_steps(from_pos, to_pos):
        diff = abs(from_pos - to_pos)
        return min(diff, n - diff)

    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    memo = {}

    def helper(i, j):
        if i == m:
            return 0
        if (i, j) in memo:
            return memo[(i, j)]
        best = float('inf')
        for k in char_positions[key[i]]:
            best = min(best, rotation_steps(j, k) + helper(i + 1, k) + 1)
        memo[(i, j)] = best
        return best

    return helper(0, 0)


# ============================================================
# Way 11: Iterative with explicit for loop
# ============================================================
def findRotateSteps_11(ring, key):
    n = len(ring)
    m = len(key)
    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    INF = float('inf')
    # dp[(i, j)] = min steps
    memo = {(m, j): 0 for j in range(n)}

    for i in range(m - 1, -1, -1):
        new_memo = {}
        for j in range(n):
            best = INF
            for k in char_positions[key[i]]:
                diff = abs(j - k)
                rot = min(diff, n - diff)
                best = min(best, rot + memo[(i + 1, k)] + 1)
            new_memo[(i, j)] = best
        memo = new_memo

    return memo[(0, 0)]


# ============================================================
# Way 12: enumerate
# ============================================================
def findRotateSteps_12(ring, key):
    n = len(ring)
    m = len(key)
    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    INF = float('inf')
    dp = [0] * n

    for i in range(m - 1, -1, -1):
        new_dp = [INF] * n
        for j in range(n):
            for k_pos in char_positions[key[i]]:
                diff = abs(j - k_pos)
                rot = min(diff, n - diff)
                new_dp[j] = min(new_dp[j], rot + dp[k_pos] + 1)
        dp = new_dp

    return dp[0]


# ============================================================
# Way 13: Tabulation by row
# ============================================================
def findRotateSteps_13(ring, key):
    n = len(ring)
    m = len(key)
    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    INF = float('inf')
    # dp[i][j]: from key position i, ring at j
    dp = [[INF] * n for _ in range(m + 1)]
    for j in range(n):
        dp[m][j] = 0

    for i in range(m - 1, -1, -1):
        target = key[i]
        positions = char_positions[target]
        for j in range(n):
            for k in positions:
                diff = abs(j - k)
                rot = min(diff, n - diff)
                dp[i][j] = min(dp[i][j], rot + dp[i + 1][k] + 1)

    return dp[0][0]


# ============================================================
# Way 14: Dijkstra-like with priority queue
# ============================================================
def findRotateSteps_14(ring, key):
    n = len(ring)
    m = len(key)
    import heapq
    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    heap = [(0, 0, 0)]
    best = {}

    while heap:
        steps, ki, rp = heapq.heappop(heap)
        if ki == m:
            return steps
        if (ki, rp) in best and best[(ki, rp)] <= steps:
            continue
        best[(ki, rp)] = steps
        for k in char_positions[key[ki]]:
            diff = abs(rp - k)
            rot = min(diff, n - diff)
            heapq.heappush(heap, (steps + rot + 1, ki + 1, k))

    return -1


# ============================================================
# Way 15: Pre-compute distances
# ============================================================
def findRotateSteps_15(ring, key):
    n = len(ring)
    m = len(key)
    # Pre-compute rotation distances
    dist = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            diff = abs(i - j)
            dist[i][j] = min(diff, n - diff)

    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    INF = float('inf')
    dp = [0] * n

    for i in range(m - 1, -1, -1):
        new_dp = [INF] * n
        target = key[i]
        for j in range(n):
            for k in char_positions[target]:
                new_dp[j] = min(new_dp[j], dist[j][k] + dp[k] + 1)
        dp = new_dp

    return dp[0]


# ============================================================
# Way 16: Bottom-up with rotation helper
# ============================================================
def findRotateSteps_16(ring, key):
    n = len(ring)
    m = len(key)

    def rotate_steps(a, b):
        diff = abs(a - b)
        return min(diff, n - diff)

    memo = {}

    def dp(i, j):
        if i == m:
            return 0
        if (i, j) in memo:
            return memo[(i, j)]
        best = float('inf')
        for k in range(n):
            if ring[k] == key[i]:
                best = min(best, rotate_steps(j, k) + dp(i + 1, k) + 1)
        memo[(i, j)] = best
        return best

    return dp(0, 0)


# ============================================================
# Way 17: Dijkstra-style with priority
# ============================================================
def findRotateSteps_17(ring, key):
    import heapq
    n = len(ring)
    m = len(key)
    if m == 0:
        return 0

    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    heap = [(0, 0, 0)]
    best = {}

    while heap:
        steps, ki, rp = heapq.heappop(heap)
        if ki == m:
            return steps
        if (ki, rp) in best and best[(ki, rp)] <= steps:
            continue
        best[(ki, rp)] = steps
        for k in char_positions[key[ki]]:
            diff = abs(rp - k)
            rot = min(diff, n - diff)
            heapq.heappush(heap, (steps + rot + 1, ki + 1, k))

    return -1


# ============================================================
# Way 18: Stateful DP
# ============================================================
def findRotateSteps_18(ring, key):
    n = len(ring)
    m = len(key)
    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    INF = float('inf')
    # Use dict for memoization
    memo = {}

    def helper(i, j):
        if i == m:
            return 0
        key_ = (i, j)
        if key_ in memo:
            return memo[key_]
        best = INF
        for k in char_positions[key[i]]:
            diff = abs(j - k)
            rot = min(diff, n - diff)
            best = min(best, rot + helper(i + 1, k) + 1)
        memo[key_] = best
        return best

    return helper(0, 0)


# ============================================================
# Way 19: Forward DP
# ============================================================
def findRotateSteps_19(ring, key):
    n = len(ring)
    m = len(key)
    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    INF = float('inf')
    # dp[i][j]: min steps to spell key[:i] ending with ring at position j
    dp = [[INF] * n for _ in range(m + 1)]
    dp[0][0] = 0  # start at position 0

    for i in range(1, m + 1):
        target = key[i - 1]
        for j in char_positions[target]:
            # From previous ring position k to j
            for k in range(n):
                if dp[i - 1][k] != INF:
                    diff = abs(k - j)
                    rot = min(diff, n - diff)
                    dp[i][j] = min(dp[i][j], dp[i - 1][k] + rot + 1)

    return min(dp[m])


# ============================================================
# Way 20: Final cleanest
# ============================================================
def findRotateSteps_20(ring, key):
    n = len(ring)
    m = len(key)
    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    INF = float('inf')
    dp = [[INF] * n for _ in range(m + 1)]
    for j in range(n):
        dp[m][j] = 0

    for i in range(m - 1, -1, -1):
        for j in range(n):
            for k in char_positions[key[i]]:
                diff = abs(j - k)
                rot = min(diff, n - diff)
                dp[i][j] = min(dp[i][j], rot + dp[i + 1][k] + 1)

    return dp[0][0]


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ("godding", "gd", 4, "Standard"),
        ("godding", "godding", 13, "Full match"),
        ("abcde", "ade", 6, "Simple"),
        ("a", "a", 1, "Single"),
        ("aaaaa", "aaa", 3, "All same"),
    ]

    implementations = [
        ("Way 1: 2D DP (BEST)", findRotateSteps_1),
        ("Way 2: Memoized recursion", findRotateSteps_2),
        ("Way 3: 1D rolling DP", findRotateSteps_3),
        ("Way 4: Brute recursion", findRotateSteps_4),
        ("Way 5: lru_cache", findRotateSteps_5),
        ("Way 6: Class-based", findRotateSteps_6),
        ("Way 7: numpy", findRotateSteps_7),
        ("Way 8: BFS", findRotateSteps_8),
        ("Way 9: min helper", findRotateSteps_9),
        ("Way 10: Helper functions", findRotateSteps_10),
        ("Way 11: Iterative", findRotateSteps_11),
        ("Way 12: enumerate", findRotateSteps_12),
        ("Way 13: Tabulation", findRotateSteps_13),
        ("Way 14: BFS deque", findRotateSteps_14),
        ("Way 15: Pre-compute dist", findRotateSteps_15),
        ("Way 16: Bottom-up", findRotateSteps_16),
        ("Way 17: Dijkstra", findRotateSteps_17),
        ("Way 18: Stateful DP", findRotateSteps_18),
        ("Way 19: Forward DP", findRotateSteps_19),
        ("Way 20: Final cleanest", findRotateSteps_20),
    ]

    for name, fn in implementations:
        passed = 0
        failed = 0
        for ring, key, expected, desc in test_cases:
            try:
                result = fn(ring, key)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    print(f"  FAIL [{name}] {desc}: ring='{ring}' key='{key}' expected={expected} got={result}")
            except Exception as e:
                failed += 1
                print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_tests()
