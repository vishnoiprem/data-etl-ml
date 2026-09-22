"""
Sum of Square Numbers - 10 Ways
================================
Given a non-negative integer c, determine whether there exist two non-negative
integers a and b such that a^2 + b^2 == c.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/sum-of-square-numbers

Examples:
    5  -> True  (1^2 + 2^2 = 5)
    4  -> True  (0^2 + 2^2)
    3  -> False
    0  -> True  (0^2 + 0^2)
    1  -> True  (0^2 + 1^2)

Constraints:
- 0 <= c <= 2^31 - 1

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Find a, b >= 0 such that a^2 + b^2 == c. Return True/False."

2. KEY INSIGHT:
   "Two-pointer on [0, sqrt(c)]. a starts at 0, b starts at floor(sqrt(c)).
    Move a inward or b inward based on a^2+b^2 vs c."

3. PATTERN RECOGNITION:
   "Two-pointer converging from both ends on a virtual array of squares."

4. EDGE CASES:
   - c == 0 -> 0^2 + 0^2 -> True.
   - c == 1 -> 0^2 + 1^2 -> True.
   - Perfect square -> True (a = 0).
   - Use integer sqrt to avoid floats: hi = isqrt(c).

5. TRICKY DETAIL:
   "Use math.isqrt(c) (Python 3.8+) for integer square root. Avoid float
    sqrt to dodge precision issues at large c."

6. ALGORITHM:
   "a, b = 0, isqrt(c)
    while a <= b:
        s = a*a + b*b
        if s == c: return True
        if s < c: a += 1
        else: b -= 1
    return False"

7. WHY TWO-POINTER:
   "a^2 is monotonically increasing in a; b^2 monotonically decreasing
    in b (as b shrinks). The sum a^2+b^2 adjusts monotonically:
    - increase a -> sum increases
    - decrease b -> sum decreases
    Hence two-pointer converges in O(sqrt(c))."

8. COMPLEXITY:
   "Time: O(sqrt(c)).
    Space: O(1)."

9. CODE STRUCTURE:
   "from math import isqrt
    a, b = 0, isqrt(c)
    while a <= b:
        ...
    return False"

10. MENTAL TRACE:
    c = 5, isqrt(5) = 2
    a=0, b=2: 0+4=4 < 5 -> a=1
    a=1, b=2: 1+4=5 == 5 -> True ✓
    c = 3
    a=0, b=1: 0+1=1 < 3 -> a=1
    a=1, b=1: 1+1=2 < 3 -> a=2 (now a>b, exit)
    return False ✓
"""


import math


# Solution 1: Canonical two-pointer (BEST)
def sum_sq_v1(c):
    a, b = 0, math.isqrt(c)
    while a <= b:
        s = a * a + b * b
        if s == c:
            return True
        if s < c:
            a += 1
        else:
            b -= 1
    return False


# Solution 2: With int(math.sqrt(c)) — float-based
def sum_sq_v2(c):
    a, b = 0, int(math.sqrt(c))
    while a <= b:
        s = a * a + b * b
        if s == c:
            return True
        if s < c:
            a += 1
        else:
            b -= 1
    return False


# Solution 3: Brute force — try all pairs
def sum_sq_v3(c):
    for a in range(math.isqrt(c) + 1):
        for b in range(math.isqrt(c) + 1):
            if a * a + b * b == c:
                return True
    return False


# Solution 4: Brute force — a in range, compute b
def sum_sq_v4(c):
    for a in range(math.isqrt(c) + 1):
        b_sq = c - a * a
        b = math.isqrt(b_sq)
        if b * b == b_sq:
            return True
    return False


# Solution 5: Binary search for b
def sum_sq_v5(c):
    def is_square(x):
        s = math.isqrt(x)
        return s * s == x

    for a in range(math.isqrt(c) + 1):
        if is_square(c - a * a):
            return True
    return False


# Solution 6: Hashmap / set-based
def sum_sq_v6(c):
    squares = set()
    for i in range(math.isqrt(c) + 1):
        squares.add(i * i)
        if (c - i * i) in squares:
            return True
    return False


# Solution 7: Using Fermat's theorem on sums of two squares
def sum_sq_v7(c):
    """A number is a sum of two squares iff in its prime factorization,
    every prime p ≡ 3 (mod 4) occurs an even number of times."""
    def factorize(n):
        factors = {}
        d = 2
        while d * d <= n:
            while n % d == 0:
                factors[d] = factors.get(d, 0) + 1
                n //= d
            d += 1
        if n > 1:
            factors[n] = factors.get(n, 0) + 1
        return factors

    if c == 0:
        return True
    factors = factorize(c)
    for p, e in factors.items():
        if p % 4 == 3 and e % 2 == 1:
            return False
    return True


# Solution 8: Recursive two-pointer
def sum_sq_v8(c):
    a, b = 0, math.isqrt(c)

    def helper(lo, hi):
        if lo > hi:
            return False
        s = lo * lo + hi * hi
        if s == c:
            return True
        if s < c:
            return helper(lo + 1, hi)
        return helper(lo, hi - 1)

    return helper(a, b)


# Solution 9: Using sorted array of squares + binary search pair
def sum_sq_v9(c):
    lo_hi = math.isqrt(c)
    squares = [i * i for i in range(lo_hi + 1)]
    # For each a, binary-search b such that a^2 + b^2 == c
    import bisect
    for a in range(lo_hi + 1):
        target = c - a * a
        idx = bisect.bisect_left(squares, target, a, len(squares))
        if idx < len(squares) and squares[idx] == target:
            return True
    return False


# Solution 10: BFS / iterative deepening
def sum_sq_v10(c):
    """Iteratively try a from 0..sqrt(c), checking if c - a^2 is a square."""
    for a in range(math.isqrt(c) + 1):
        # Inline is_square check
        target = c - a * a
        if target < 0:
            break
        s = math.isqrt(target)
        if s * s == target:
            return True
    return False


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (2ptr + isqrt)",        sum_sq_v1),
        ("V2 (2ptr + sqrt float)",    sum_sq_v2),
        ("V3 (brute double loop)",    sum_sq_v3),
        ("V4 (brute a only)",         sum_sq_v4),
        ("V5 (binary search)",        sum_sq_v5),
        ("V6 (set lookup)",           sum_sq_v6),
        ("V7 (Fermat's theorem)",     sum_sq_v7),
        ("V8 (recursive 2ptr)",       sum_sq_v8),
        ("V9 (precomputed+sorted)",   sum_sq_v9),
        ("V10 (iterative deepening)", sum_sq_v10),
    ]

    test_cases = [
        # (c, expected)
        (5,  True),
        (4,  True),
        (3,  False),
        (0,  True),
        (1,  True),
        (2,  True),
        (10, True),    # 1 + 9
        (13, True),    # 4 + 9
        (25, True),    # 0 + 25
        (100, True),   # 36 + 64
        (999, False),
        (50, True),    # 1 + 49 or 25 + 25
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (c, expected) in enumerate(test_cases):
            try:
                got = func(c)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: c={c} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
    print("\n=== INTERVIEW THINKING ===")
    print("""
1. UNDERSTAND:  Find a, b >= 0 with a^2+b^2 == c.
2. INSIGHT:     Two-pointer on [0, isqrt(c)]; a^2 monotonic.
3. PATTERN:     Convergent two-pointer; O(sqrt(c)) time.
4. EDGE:        c=0 -> True; perfect square -> True; c=1 -> True.
5. TRICKY:      Use math.isqrt() for integer sqrt; avoid float precision.
6. ALGORITHM:   a=0, b=isqrt(c); while a<=b: compute s; adjust.
7. PROOF:       a^2 increases with a; b^2 decreases with b; sum monotonic in each direction.
8. COMPLEXITY:  O(sqrt(c)) time, O(1) space.
9. CODE:        math.isqrt + while a<=b.
10. TRACE:      c=5: (0,2)->4<5, a=1; (1,2)->5==5 -> True.
""")
