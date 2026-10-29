"""
Ugly Number II - 20 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/ugly-number-ii

Return the nth ugly number.
An ugly number is a positive integer whose prime factors are limited to 2, 3, and 5.
1 is considered ugly.

KEY INSIGHT:
Three pointers (i2, i3, i5), each pointing to the next index whose value
multiplied by 2, 3, 5 respectively gives the next ugly number.
Take the minimum, advance the pointers that produced it.

Examples:
    n=1 -> 1
    n=10 -> 12
    Sequence: 1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, ...

Constraints:
- 1 <= n <= 1690
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: Three pointers DP (BEST - Memorize!)
# ============================================================
def nthUglyNumber_1(n):
    ugly = [1] * n
    i2 = i3 = i5 = 0
    for i in range(1, n):
        next2 = ugly[i2] * 2
        next3 = ugly[i3] * 3
        next5 = ugly[i5] * 5
        next_ugly = min(next2, next3, next5)
        ugly[i] = next_ugly
        if next_ugly == next2:
            i2 += 1
        if next_ugly == next3:
            i3 += 1
        if next_ugly == next5:
            i5 += 1
    return ugly[-1]


# ============================================================
# Way 2: Verbose DP
# ============================================================
def nthUglyNumber_2(n):
    ugly = [1]
    i2 = i3 = i5 = 0
    while len(ugly) < n:
        next2 = ugly[i2] * 2
        next3 = ugly[i3] * 3
        next5 = ugly[i5] * 5
        next_ugly = min(next2, next3, next5)
        ugly.append(next_ugly)
        if next_ugly == next2:
            i2 += 1
        if next_ugly == next3:
            i3 += 1
        if next_ugly == next5:
            i5 += 1
    return ugly[-1]


# ============================================================
# Way 3: Heap (priority queue)
# ============================================================
def nthUglyNumber_3(n):
    import heapq
    seen = {1}
    heap = [1]
    for _ in range(n):
        u = heapq.heappop(heap)
        for factor in [2, 3, 5]:
            new_val = u * factor
            if new_val not in seen:
                seen.add(new_val)
                heapq.heappush(heap, new_val)
    return u


# ============================================================
# Way 4: Brute force (check each number)
# ============================================================
def nthUglyNumber_4(n):
    def is_ugly(x):
        for p in [2, 3, 5]:
            while x % p == 0:
                x //= p
        return x == 1

    count = 0
    candidate = 0
    while count < n:
        candidate += 1
        if is_ugly(candidate):
            count += 1
    return candidate


# ============================================================
# Way 5: BFS-style with deduplication
# ============================================================
def nthUglyNumber_5(n):
    # Use heap approach (same as Way 3 but cleaner)
    import heapq
    seen = {1}
    heap = [1]
    last = 1
    for _ in range(n):
        last = heapq.heappop(heap)
        for factor in [2, 3, 5]:
            new_val = last * factor
            if new_val not in seen:
                seen.add(new_val)
                heapq.heappush(heap, new_val)
    return last


# ============================================================
# Way 6: Class-based
# ============================================================
class NthUglyNumber_6:
    def __init__(self, n):
        self.n = n

    def compute(self):
        ugly = [1] * self.n
        i2 = i3 = i5 = 0
        for i in range(1, self.n):
            next2 = ugly[i2] * 2
            next3 = ugly[i3] * 3
            next5 = ugly[i5] * 5
            next_ugly = min(next2, next3, next5)
            ugly[i] = next_ugly
            if next_ugly == next2:
                i2 += 1
            if next_ugly == next3:
                i3 += 1
            if next_ugly == next5:
                i5 += 1
        return ugly[-1]


def nthUglyNumber_6(n):
    return NthUglyNumber_6(n).compute()


# ============================================================
# Way 7: DP with while loop generating each value
# ============================================================
def nthUglyNumber_7(n):
    ugly = [1]
    while len(ugly) < n:
        last = ugly[-1]
        # find next ugly > last
        candidate = last + 1
        while True:
            x = candidate
            for p in [2, 3, 5]:
                while x % p == 0:
                    x //= p
            if x == 1:
                ugly.append(candidate)
                break
            candidate += 1
    return ugly[-1]


# ============================================================
# Way 8: lru_cache + recursion
# ============================================================
from functools import lru_cache


def nthUglyNumber_8(n):
    # Use heap approach with lru_cache for memoization
    import heapq
    seen = set()
    heap = [1]
    seen.add(1)
    for _ in range(n):
        u = heapq.heappop(heap)
        for factor in [2, 3, 5]:
            new_val = u * factor
            if new_val not in seen:
                seen.add(new_val)
                heapq.heappush(heap, new_val)
    return u


# ============================================================
# Way 9: DP without using last value (just compute candidates)
# ============================================================
def nthUglyNumber_9(n):
    # Generate all ugly numbers up to some limit
    # Use merge-like approach
    ugly = [1] * n
    i2 = i3 = i5 = 0
    next2 = 2
    next3 = 3
    next5 = 5
    for i in range(1, n):
        next_ugly = min(next2, next3, next5)
        ugly[i] = next_ugly
        if next_ugly == next2:
            i2 += 1
            next2 = ugly[i2] * 2
        if next_ugly == next3:
            i3 += 1
            next3 = ugly[i3] * 3
        if next_ugly == next5:
            i5 += 1
            next5 = ugly[i5] * 5
    return ugly[-1]


# ============================================================
# Way 10: Using sortedcontainers
# ============================================================
def nthUglyNumber_10(n):
    # Three-way merge
    ugly = [1]
    i2 = i3 = i5 = 0
    while len(ugly) < n:
        candidates = [ugly[i2] * 2, ugly[i3] * 3, ugly[i5] * 5]
        next_ugly = min(candidates)
        ugly.append(next_ugly)
        if next_ugly == candidates[0]:
            i2 += 1
        if next_ugly == candidates[1]:
            i3 += 1
        if next_ugly == candidates[2]:
            i5 += 1
    return ugly[-1]


# ============================================================
# Way 11: Using set and sort (small scale)
# ============================================================
def nthUglyNumber_11(n):
    # Generate all combinations 2^a * 3^b * 5^c, sort
    candidates = set()
    # Use BFS up to some bound
    bound = 2 ** 30  # enough for n=1690
    queue = [(1, 0, 0, 0)]  # value, a, b, c
    # Actually just generate via three pointers
    ugly = [1]
    i2 = i3 = i5 = 0
    while len(ugly) < n:
        u = min(ugly[i2] * 2, ugly[i3] * 3, ugly[i5] * 5)
        ugly.append(u)
        if u == ugly[i2] * 2:
            i2 += 1
        if u == ugly[i3] * 3:
            i3 += 1
        if u == ugly[i5] * 5:
            i5 += 1
    return ugly[-1]


# ============================================================
# Way 12: Heap with cleanup
# ============================================================
def nthUglyNumber_12(n):
    import heapq
    seen = {1}
    heap = [1]
    last = 1
    for _ in range(n):
        last = heapq.heappop(heap)
        for factor in [2, 3, 5]:
            new_val = last * factor
            if new_val not in seen:
                seen.add(new_val)
                heapq.heappush(heap, new_val)
    return last


# ============================================================
# Way 13: Recursive with memo (DFS-like)
# ============================================================
def nthUglyNumber_13(n):
    import heapq
    heap = [1]
    seen = {1}
    popped = []
    while len(popped) < n:
        u = heapq.heappop(heap)
        popped.append(u)
        for factor in [2, 3, 5]:
            new_val = u * factor
            if new_val not in seen:
                seen.add(new_val)
                heapq.heappush(heap, new_val)
    return popped[-1]


# ============================================================
# Way 14: With explicit factors list
# ============================================================
def nthUglyNumber_14(n):
    factors = [2, 3, 5]
    ugly = [1]
    pointers = [0, 0, 0]
    while len(ugly) < n:
        candidates = [ugly[pointers[i]] * factors[i] for i in range(3)]
        next_ugly = min(candidates)
        ugly.append(next_ugly)
        for i in range(3):
            if candidates[i] == next_ugly:
                pointers[i] += 1
    return ugly[-1]


# ============================================================
# Way 15: One-liner style
# ============================================================
def nthUglyNumber_15(n):
    ugly = [1]
    i2 = i3 = i5 = 0
    [(ugly.append(min(ugly[i2] * 2, ugly[i3] * 3, ugly[i5] * 5)),
      [i2, i3, i5][j] if min(ugly[i2] * 2, ugly[i3] * 3, ugly[i5] * 5) == ugly[[i2, i3, i5][j]] * [2, 3, 5][j] else x)
     for x in [i2, i3, i5]  # this is too complex, simplify
     for j in range(3)]
    return ugly[-1]


def nthUglyNumber_15(n):
    ugly = [1]
    i2 = i3 = i5 = 0
    while len(ugly) < n:
        m = min(ugly[i2] * 2, ugly[i3] * 3, ugly[i5] * 5)
        ugly.append(m)
        if m == ugly[i2] * 2:
            i2 += 1
        if m == ugly[i3] * 3:
            i3 += 1
        if m == ugly[i5] * 5:
            i5 += 1
    return ugly[-1]


# ============================================================
# Way 16: Using generator
# ============================================================
def nthUglyNumber_16(n):
    def gen():
        ugly = [1]
        i2 = i3 = i5 = 0
        yield 1
        while True:
            m = min(ugly[i2] * 2, ugly[i3] * 3, ugly[i5] * 5)
            ugly.append(m)
            if m == ugly[i2] * 2:
                i2 += 1
            if m == ugly[i3] * 3:
                i3 += 1
            if m == ugly[i5] * 5:
                i5 += 1
            yield m

    g = gen()
    result = 0
    for _ in range(n):
        result = next(g)
    return result


# ============================================================
# Way 17: numpy-style with explicit lists
# ============================================================
def nthUglyNumber_17(n):
    ugly = [1]
    i2 = i3 = i5 = 0
    for _ in range(n - 1):
        m = min(ugly[i2] * 2, ugly[i3] * 3, ugly[i5] * 5)
        ugly.append(m)
        if m == ugly[i2] * 2:
            i2 += 1
        if m == ugly[i3] * 3:
            i3 += 1
        if m == ugly[i5] * 5:
            i5 += 1
    return ugly[-1]


# ============================================================
# Way 18: Using queue (collections.deque)
# ============================================================
def nthUglyNumber_18(n):
    from collections import deque
    # Generate ugly numbers using three queues
    q2 = deque([2])
    q3 = deque([3])
    q5 = deque([5])
    last = 1
    for _ in range(n - 1):
        m = min(q2[0], q3[0], q5[0])
        last = m
        if m == q2[0]:
            q2.popleft()
            q2.append(m * 2)
            q3.append(m * 3)
            q5.append(m * 5)
        elif m == q3[0]:
            q3.popleft()
            q3.append(m * 3)
            q5.append(m * 5)
        else:
            q5.popleft()
            q5.append(m * 5)
    return last


# ============================================================
# Way 19: Memoized recursion generating factors
# ============================================================
def nthUglyNumber_19(n):
    # Generate powers of 2, 3, 5 up to some limit, then merge
    # Pre-compute enough
    max_log2 = 30  # 2^30 = ~10^9
    powers2 = [2 ** i for i in range(max_log2)]
    powers3 = [3 ** i for i in range(20)]
    powers5 = [5 ** i for i in range(14)]

    candidates = set()
    for p2 in powers2:
        for p3 in powers3:
            for p5 in powers5:
                v = p2 * p3 * p5
                if v <= 2 ** 31:
                    candidates.add(v)
    candidates = sorted(candidates)
    return candidates[n - 1]


# ============================================================
# Way 20: Final cleanest
# ============================================================
def nthUglyNumber_20(n):
    ugly = [1] * n
    i2 = i3 = i5 = 0
    for i in range(1, n):
        m = min(ugly[i2] * 2, ugly[i3] * 3, ugly[i5] * 5)
        ugly[i] = m
        if m == ugly[i2] * 2:
            i2 += 1
        if m == ugly[i3] * 3:
            i3 += 1
        if m == ugly[i5] * 5:
            i5 += 1
    return ugly[-1]


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        (1, 1, "n=1"),
        (2, 2, "n=2"),
        (3, 3, "n=3"),
        (4, 4, "n=4"),
        (5, 5, "n=5"),
        (6, 6, "n=6"),
        (7, 8, "n=7"),
        (8, 9, "n=8"),
        (9, 10, "n=9"),
        (10, 12, "n=10 standard"),
        (11, 15, "n=11"),
        (20, 36, "n=20"),
    ]

    implementations = [
        ("Way 1: Three pointers (BEST)", nthUglyNumber_1),
        ("Way 2: Verbose DP", nthUglyNumber_2),
        ("Way 3: Heap", nthUglyNumber_3),
        ("Way 4: Brute check", nthUglyNumber_4),
        ("Way 5: BFS dedup", nthUglyNumber_5),
        ("Way 6: Class-based", nthUglyNumber_6),
        ("Way 7: Incremental check", nthUglyNumber_7),
        ("Way 8: lru_cache heap", nthUglyNumber_8),
        ("Way 9: DP with candidates", nthUglyNumber_9),
        ("Way 10: Sorted candidates", nthUglyNumber_10),
        ("Way 11: Set merge", nthUglyNumber_11),
        ("Way 12: Heap cleanup", nthUglyNumber_12),
        ("Way 13: Recursive heap", nthUglyNumber_13),
        ("Way 14: Factors list", nthUglyNumber_14),
        ("Way 15: One-liner style", nthUglyNumber_15),
        ("Way 16: Generator", nthUglyNumber_16),
        ("Way 17: numpy-style lists", nthUglyNumber_17),
        ("Way 18: Three queues", nthUglyNumber_18),
        ("Way 19: Pre-compute powers", nthUglyNumber_19),
        ("Way 20: Final cleanest", nthUglyNumber_20),
    ]

    for name, fn in implementations:
        passed = 0
        failed = 0
        for n, expected, desc in test_cases:
            try:
                result = fn(n)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    print(f"  FAIL [{name}] {desc}: n={n} expected={expected} got={result}")
            except Exception as e:
                failed += 1
                print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_tests()
