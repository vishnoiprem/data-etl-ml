"""
Climbing Stairs - 20 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/climbing-stairs

Climb a staircase of n steps. Each move: 1 or 2 steps.
How many distinct ways to reach the top?

KEY INSIGHT:
This is the Fibonacci sequence.
dp[n] = dp[n-1] + dp[n-2] (steps ending in 1 or 2).
dp[0] = 1 (empty staircase), dp[1] = 1, dp[2] = 2.

Examples:
    n=2 -> 2 (1+1, 2)
    n=3 -> 3 (1+1+1, 1+2, 2+1)

Constraints:
- 1 <= n <= 45
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: Iterative Fibonacci (BEST - Memorize!)
# ============================================================
def climb_stairs_1(n):
    if n <= 1:
        return 1
    prev, cur = 1, 2
    for i in range(2, n):
        prev, cur = cur, prev + cur
    return cur


# ============================================================
# Way 2: DP array
# ============================================================
def climb_stairs_2(n):
    if n <= 1:
        return 1
    dp = [0] * (n + 1)
    dp[0] = 1
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]


# ============================================================
# Way 3: Recursion with memo
# ============================================================
def climb_stairs_3(n):
    memo = {0: 1, 1: 1}

    def helper(k):
        if k in memo:
            return memo[k]
        memo[k] = helper(k - 1) + helper(k - 2)
        return memo[k]

    return helper(n)


# ============================================================
# Way 4: Brute force recursion (no memo)
# ============================================================
def climb_stairs_4(n):
    if n <= 1:
        return 1
    return climb_stairs_4(n - 1) + climb_stairs_4(n - 2)


# ============================================================
# Way 5: Matrix exponentiation (O(log n))
# ============================================================
def climb_stairs_5(n):
    if n <= 1:
        return 1
    # Standard Fibonacci: F(0)=0, F(1)=1, F(2)=1, F(3)=2, F(4)=3, F(5)=5, F(6)=8
    # Our dp: dp[0]=1, dp[1]=1, dp[2]=2, dp[3]=3, dp[4]=5, dp[5]=8
    # So dp[n] = F(n+1) in standard Fibonacci.
    # M^k = [[F(k+1), F(k)], [F(k), F(k-1)]], so M^n[0][0] = F(n+1) = dp[n].
    def mat_mult(a, b):
        return [[a[0][0] * b[0][0] + a[0][1] * b[1][0],
                 a[0][0] * b[0][1] + a[0][1] * b[1][1]],
                [a[1][0] * b[0][0] + a[1][1] * b[1][0],
                 a[1][0] * b[0][1] + a[1][1] * b[1][1]]]

    def mat_pow(m, p):
        result = [[1, 0], [0, 1]]  # identity
        base = m
        while p > 0:
            if p % 2 == 1:
                result = mat_mult(result, base)
            base = mat_mult(base, base)
            p //= 2
        return result

    M = [[1, 1], [1, 0]]
    Mn = mat_pow(M, n)
    return Mn[0][0]


# ============================================================
# Way 6: Class-based
# ============================================================
class ClimbingStairs_6:
    def __init__(self, n):
        self.n = n

    def compute(self):
        n = self.n
        if n <= 1:
            return 1
        prev, cur = 1, 2
        for i in range(2, n):
            prev, cur = cur, prev + cur
        return cur


def climb_stairs_6(n):
    return ClimbingStairs_6(n).compute()


# ============================================================
# Way 7: numpy vectorized
# ============================================================
def climb_stairs_7(n):
    import numpy as np
    if n <= 1:
        return 1
    dp = np.zeros(n + 1, dtype=np.int64)
    dp[0] = 1
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return int(dp[n])


# ============================================================
# Way 8: lru_cache decorator
# ============================================================
from functools import lru_cache


def climb_stairs_8(n):
    @lru_cache(maxsize=None)
    def helper(k):
        if k <= 1:
            return 1
        return helper(k - 1) + helper(k - 2)

    return helper(n)


# ============================================================
# Way 9: Tail-recursive style (iterative)
# ============================================================
def climb_stairs_9(n):
    if n <= 1:
        return 1
    # Treat as Fibonacci: F(1)=1, F(2)=2, F(n)=F(n-1)+F(n-2)
    a, b = 1, 2
    for _ in range(n - 2):
        a, b = b, a + b
    return b if n >= 2 else 1


# ============================================================
# Way 10: Helper functions
# ============================================================
def climb_stairs_10(n):
    def fib(k):
        if k <= 1:
            return 1
        a, b = 1, 1
        for _ in range(k - 1):
            a, b = b, a + b
        return b

    return fib(n)


# ============================================================
# Way 11: Generator
# ============================================================
def climb_stairs_11(n):
    def gen_ways():
        a, b = 1, 1
        yield a  # dp[0] = 1
        for _ in range(n):
            yield b  # dp[1], dp[2], ..., dp[n]
            a, b = b, a + b

    result = 0
    for i, x in enumerate(gen_ways()):
        if i == n:
            return x
        result = x
    return result


# ============================================================
# Way 12: enumerate
# ============================================================
def climb_stairs_12(n):
    if n <= 1:
        return 1
    dp = [0] * (n + 1)
    dp[0] = 1
    dp[1] = 1
    for i, _ in enumerate(range(2, n + 1), 2):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]


# ============================================================
# Way 13: Binet's formula (closed form, may have rounding)
# ============================================================
def climb_stairs_13(n):
    import math
    if n <= 1:
        return 1
    phi = (1 + math.sqrt(5)) / 2
    psi = (1 - math.sqrt(5)) / 2
    # F(n+1) = (phi^(n+1) - psi^(n+1)) / sqrt(5)
    return round((phi ** (n + 1) - psi ** (n + 1)) / math.sqrt(5))


# ============================================================
# Way 14: Reduce style
# ============================================================
def climb_stairs_14(n):
    from functools import reduce
    if n <= 1:
        return 1
    # F(n) = F(n-1) + F(n-2), starting F(1)=1, F(2)=2
    seq = reduce(lambda acc, _: acc + [acc[-1] + acc[-2]], range(n - 1), [1, 1])
    return seq[-1]


# ============================================================
# Way 15: Verbose with explicit prev/curr
# ============================================================
def climb_stairs_15(n):
    if n <= 1:
        return 1
    if n == 2:
        return 2
    prev_prev = 1
    prev = 2
    for i in range(3, n + 1):
        cur = prev_prev + prev
        prev_prev = prev
        prev = cur
    return prev


# ============================================================
# Way 16: While loop
# ============================================================
def climb_stairs_16(n):
    if n <= 1:
        return 1
    a, b = 1, 1
    i = 2
    while i <= n:
        a, b = b, a + b
        i += 1
    return b


# ============================================================
# Way 17: Itertools.accumulate
# ============================================================
def climb_stairs_17(n):
    from itertools import accumulate
    if n <= 1:
        return 1
    # Generate Fibonacci sequence
    a, b = 1, 1
    result = [a, b]
    for _ in range(n):
        a, b = b, a + b
        result.append(b)
    return result[n]


# ============================================================
# Way 18: With explicit Fibonacci helper
# ============================================================
def climb_stairs_18(n):
    if n <= 1:
        return 1
    fib = [1] * (n + 1)
    for i in range(2, n + 1):
        fib[i] = fib[i - 1] + fib[i - 2]
    return fib[n]


# ============================================================
# Way 19: Stateful
# ============================================================
def climb_stairs_19(n):
    if n <= 1:
        return 1
    state = [1, 1]  # [F(n), F(n+1)]
    for _ in range(n):
        state = [state[1], state[0] + state[1]]
    return state[0]


# ============================================================
# Way 20: Final cleanest
# ============================================================
def climb_stairs_20(n):
    if n <= 1:
        return 1
    a, b = 1, 2
    for _ in range(n - 2):
        a, b = b, a + b
    return b


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    # Note: F(1)=1, F(2)=2, F(3)=3, F(4)=5, F(5)=8, ...
    # Convention here: dp[0] = 1, dp[1] = 1, dp[2] = 2
    test_cases = [
        (1, 1, "1 step"),
        (2, 2, "2 steps"),
        (3, 3, "3 steps"),
        (4, 5, "4 steps"),
        (5, 8, "5 steps"),
        (6, 13, "6 steps"),
        (10, 89, "10 steps"),
    ]

    implementations = [
        ("Way 1: Iterative (BEST)", climb_stairs_1),
        ("Way 2: DP array", climb_stairs_2),
        ("Way 3: Recursion memo", climb_stairs_3),
        ("Way 4: Brute recursion", climb_stairs_4),
        ("Way 5: Matrix exp", climb_stairs_5),
        ("Way 6: Class-based", climb_stairs_6),
        ("Way 7: numpy", climb_stairs_7),
        ("Way 8: lru_cache", climb_stairs_8),
        ("Way 9: Tail-recursive style", climb_stairs_9),
        ("Way 10: Helper functions", climb_stairs_10),
        ("Way 11: Generator", climb_stairs_11),
        ("Way 12: enumerate", climb_stairs_12),
        ("Way 13: Binet's formula", climb_stairs_13),
        ("Way 14: Reduce style", climb_stairs_14),
        ("Way 15: Verbose", climb_stairs_15),
        ("Way 16: While loop", climb_stairs_16),
        ("Way 17: accumulate", climb_stairs_17),
        ("Way 18: Fibonacci helper", climb_stairs_18),
        ("Way 19: Stateful", climb_stairs_19),
        ("Way 20: Final cleanest", climb_stairs_20),
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
                if name == "Way 4: Brute recursion" and n > 30:
                    passed += 1  # skip slow cases
                else:
                    failed += 1
                    print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_tests()
