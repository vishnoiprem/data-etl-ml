"""
Counting Bits - 20 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/counting-bits

For each x in [0, n], return the count of 1s in the binary representation.

KEY INSIGHT:
- dp[x] = dp[x >> 1] + (x & 1)  (drop last bit + last bit).
- Or: dp[x] = dp[x & (x-1)] + 1  (drop lowest set bit + 1 for it).
- Or: dp[x] = 1 + dp[x - lowest_power_of_2].

Examples:
    n=2 -> [0, 1, 1]
    n=5 -> [0, 1, 1, 2, 1, 2]

Constraints:
- 0 <= n <= 10^4
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: DP with x & (x-1) trick (BEST - Memorize!)
# ============================================================
def counting_bits_1(n):
    dp = [0] * (n + 1)
    for x in range(1, n + 1):
        dp[x] = dp[x & (x - 1)] + 1
    return dp


# ============================================================
# Way 2: DP with x >> 1 (drop last bit)
# ============================================================
def counting_bits_2(n):
    dp = [0] * (n + 1)
    for x in range(1, n + 1):
        dp[x] = dp[x >> 1] + (x & 1)
    return dp


# ============================================================
# Way 3: Verbose (just call bin().count('1'))
# ============================================================
def counting_bits_3(n):
    return [bin(x).count('1') for x in range(n + 1)]


# ============================================================
# Way 4: Verbose DP with explicit mask
# ============================================================
def counting_bits_4(n):
    dp = [0] * (n + 1)
    for x in range(1, n + 1):
        # dp[x] = 1 + dp[x - lowest_power_of_2]
        lowest = x & -x
        dp[x] = 1 + dp[x - lowest]
    return dp


# ============================================================
# Way 5: Brute force popcount
# ============================================================
def counting_bits_5(n):
    result = []
    for x in range(n + 1):
        count = 0
        y = x
        while y:
            count += y & 1
            y >>= 1
        result.append(count)
    return result


# ============================================================
# Way 6: Class-based
# ============================================================
class CountingBits_6:
    def __init__(self, n):
        self.n = n

    def compute(self):
        dp = [0] * (self.n + 1)
        for x in range(1, self.n + 1):
            dp[x] = dp[x & (x - 1)] + 1
        return dp


def counting_bits_6(n):
    return CountingBits_6(n).compute()


# ============================================================
# Way 7: numpy vectorized
# ============================================================
def counting_bits_7(n):
    import numpy as np
    arr = np.arange(n + 1, dtype=np.int32)
    result = np.zeros(n + 1, dtype=np.int32)
    x = arr.copy()
    while x.any():
        result += (x & 1)
        x >>= 1
    return result.tolist()


# ============================================================
# Way 8: Recursive with memo
# ============================================================
def counting_bits_8(n):
    memo = {0: 0}

    def helper(x):
        if x in memo:
            return memo[x]
        memo[x] = helper(x & (x - 1)) + 1
        return memo[x]

    return [helper(x) for x in range(n + 1)]


# ============================================================
# Way 9: lru_cache decorator
# ============================================================
from functools import lru_cache


def counting_bits_9(n):
    @lru_cache(maxsize=None)
    def count(x):
        if x == 0:
            return 0
        return count(x & (x - 1)) + 1

    return [count(x) for x in range(n + 1)]


# ============================================================
# Way 10: Helper functions
# ============================================================
def counting_bits_10(n):
    def popcount(x):
        count = 0
        while x:
            x &= (x - 1)
            count += 1
        return count

    return [popcount(x) for x in range(n + 1)]


# ============================================================
# Way 11: Using x & (x-1) (same as Way 1)
# ============================================================
def counting_bits_11(n):
    dp = [0] * (n + 1)
    for x in range(1, n + 1):
        dp[x] = dp[x & (x - 1)] + 1
    return dp


# ============================================================
# Way 12: BFS / iterative using x & -x
# ============================================================
def counting_bits_12(n):
    result = [0]
    for x in range(1, n + 1):
        # x & -x isolates the lowest set bit
        result.append(1 + result[x - (x & -x)])
    return result


# ============================================================
# Way 13: Lookup table for 8-bit chunks
# ============================================================
def counting_bits_13(n):
    # Pre-compute popcount for 0..255
    lookup = [bin(i).count('1') for i in range(256)]

    result = []
    for x in range(n + 1):
        count = 0
        while x:
            count += lookup[x & 0xFF]
            x >>= 8
        result.append(count)
    return result


# ============================================================
# Way 14: Built-in bit_count (Python 3.10+)
# ============================================================
def counting_bits_14(n):
    return [x.bit_count() for x in range(n + 1)]


# ============================================================
# Way 15: Divide by 2 iteratively
# ============================================================
def counting_bits_15(n):
    result = []
    for x in range(n + 1):
        count = 0
        y = x
        while y > 0:
            count += y & 1
            y //= 2
        result.append(count)
    return result


# ============================================================
# Way 16: Using string conversion with format
# ============================================================
def counting_bits_16(n):
    return [bin(x).count('1') for x in range(n + 1)]


# ============================================================
# Way 17: DP with doubling pattern
# ============================================================
def counting_bits_17(n):
    # dp[2k] = dp[k], dp[2k+1] = dp[k] + 1
    dp = [0] * (n + 1)
    for x in range(1, n + 1):
        dp[x] = dp[x >> 1] + (x & 1)
    return dp


# ============================================================
# Way 18: DP using x & (x-1)
# ============================================================
def counting_bits_18(n):
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        dp[i] = dp[i & (i - 1)] + 1
    return dp


# ============================================================
# Way 19: Functional with map
# ============================================================
def counting_bits_19(n):
    return list(map(lambda x: bin(x).count('1'), range(n + 1)))


# ============================================================
# Way 20: Final cleanest (the one to memorize)
# ============================================================
def counting_bits_20(n):
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        dp[i] = dp[i & (i - 1)] + 1
    return dp


# ============================================================
# HOW TO THINK (Framework)
# ============================================================
"""
HOW TO THINK ABOUT THIS PROBLEM:

1. UNDERSTAND:
   - For each x in [0, n], count set bits in binary.
   - Output array of length n+1.

2. THE TRICK:
   - Recurrence: popcount(x) = popcount(x & (x-1)) + 1.
   - x & (x-1) clears the LOWEST set bit.
   - So popcount(x) = popcount(x with lowest bit removed) + 1 (for that bit).
   - Base: popcount(0) = 0.

3. WHY THIS WORKS:
   - Each step removes exactly one set bit.
   - The number of removals = number of set bits.

4. ALTERNATIVE RECURRENCES:
   - popcount(x) = popcount(x >> 1) + (x & 1).
   - popcount(x) = popcount(x - lowest_power_of_2) + 1.

5. COMPLEXITY:
   - Time: O(n) - one pass.
   - Space: O(n) for dp array.
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        # (n, expected, description)
        (0, [0], "Just 0"),
        (1, [0, 1], "n=1"),
        (2, [0, 1, 1], "n=2 standard"),
        (5, [0, 1, 1, 2, 1, 2], "n=5 standard"),
        (8, [0, 1, 1, 2, 1, 2, 2, 3, 1], "n=8 power of 2"),
        (10, [0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2], "n=10"),
    ]

    implementations = [
        ("Way 1: x & (x-1) DP (BEST)", counting_bits_1),
        ("Way 2: x >> 1 DP", counting_bits_2),
        ("Way 3: bin count", counting_bits_3),
        ("Way 4: lowest power of 2", counting_bits_4),
        ("Way 5: Brute popcount", counting_bits_5),
        ("Way 6: Class-based", counting_bits_6),
        ("Way 7: numpy", counting_bits_7),
        ("Way 8: Recursive memo", counting_bits_8),
        ("Way 9: lru_cache", counting_bits_9),
        ("Way 10: Helper functions", counting_bits_10),
        ("Way 11: bit_length trick", counting_bits_11),
        ("Way 12: x & -x", counting_bits_12),
        ("Way 13: Lookup table", counting_bits_13),
        ("Way 14: bit_count", counting_bits_14),
        ("Way 15: Divide by 2", counting_bits_15),
        ("Way 16: format string", counting_bits_16),
        ("Way 17: Doubling pattern", counting_bits_17),
        ("Way 18: One-liner DP", counting_bits_18),
        ("Way 19: map", counting_bits_19),
        ("Way 20: Final cleanest", counting_bits_20),
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
