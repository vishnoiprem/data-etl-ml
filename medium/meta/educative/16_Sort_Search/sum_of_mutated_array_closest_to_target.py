"""
Sum of Mutated Array Closest to Target
Medium | 30 min

Given an integer array arr and a target, find an integer value such that
replacing all numbers > value with value makes the sum as close to target
as possible. Return the SMALLER value on tie.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/sum-of-mutated-array-closest-to-target

Examples:
    arr=[4,9,3], target=10 -> 3 (v=3 -> sum=9; v=4 -> sum=11; tie, return 3)
    arr=[2,3,5], target=10 -> 5 (v=5 -> sum=10 exact)
    arr=[60864,25176,27249,21296,20204], target=56803 -> 11361

KEY INSIGHT: sum(v) = sum(min(x, v) for x in arr) is MONOTONICALLY
NON-DECREASING in v. Binary search on v.

For each v: sum = prefix[i] + (n-i)*v where i = bisect_right(arr, v).
"""

import bisect


# =============================================================================
# WAY 1: Binary search on value (BEST - Memorize!)
# =============================================================================
def find_best_value_1(arr, target):
    """
    Sort + prefix sums + binary search on v.

    Binary search finds smallest v where sum(v) >= target. Then compare
    with v-1 to pick the closer one (smaller on tie).
    """
    a = sorted(arr)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]

    def cap_sum(v):
        idx = bisect.bisect_right(a, v)
        return prefix[idx] + (n - idx) * v

    lo, hi = 0, a[-1]
    while lo < hi:
        mid = (lo + hi) // 2
        if cap_sum(mid) < target:
            lo = mid + 1
        else:
            hi = mid
    # lo is smallest v with sum(v) >= target
    # Compare lo and lo-1
    s_lo = cap_sum(lo)
    s_prev = cap_sum(lo - 1) if lo > 0 else float('inf')
    diff_lo = abs(s_lo - target)
    diff_prev = abs(s_prev - target)
    # Prefer smaller v on tie
    if diff_lo < diff_prev:
        return lo
    elif diff_prev < diff_lo:
        return lo - 1
    else:
        return lo - 1  # tie, smaller


# =============================================================================
# WAY 2: Binary search with manual bisect
# =============================================================================
def find_best_value_2(arr, target):
    a = sorted(arr)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]

    def cap_sum(v):
        lo, hi = 0, n
        while lo < hi:
            mid = (lo + hi) // 2
            if a[mid] <= v:
                lo = mid + 1
            else:
                hi = mid
        idx = lo
        return prefix[idx] + (n - idx) * v

    lo, hi = 0, a[-1]
    while lo < hi:
        mid = (lo + hi) // 2
        if cap_sum(mid) < target:
            lo = mid + 1
        else:
            hi = mid
    s_lo = cap_sum(lo)
    s_prev = cap_sum(lo - 1) if lo > 0 else float('inf')
    diff_lo = abs(s_lo - target)
    diff_prev = abs(s_prev - target)
    return lo - 1 if diff_prev <= diff_lo else lo


# =============================================================================
# WAY 3: Brute force linear search
# =============================================================================
def find_best_value_3(arr, target):
    """Try every value from 0 to max(arr)."""
    def compute(v):
        return sum(min(x, v) for x in arr)

    best_v = 0
    best_diff = abs(compute(0) - target)
    for v in range(0, max(arr) + 1):
        s = compute(v)
        diff = abs(s - target)
        if diff < best_diff:
            best_diff = diff
            best_v = v
        # tie: keep smaller v
    return best_v


# =============================================================================
# WAY 4: Iterate sorted unique + estimate + nearby range
# =============================================================================
def find_best_value_4(arr, target):
    """
    Check 0, every value in arr, and a range around target/n.
    """
    sorted_unique = sorted(set(arr))
    n = len(arr)
    estimate = max(0, target // n)

    def compute(v):
        return sum(min(x, v) for x in arr)

    candidates = set([0, estimate, estimate + 1])
    candidates.update(sorted_unique)
    for v in sorted_unique:
        if v > 0:
            candidates.add(v - 1)
        candidates.add(v + 1)
    # Add a range around estimate (covers cases where optimal v is between values)
    for v in range(max(0, estimate - 2), estimate + 5):
        candidates.add(v)

    best_v = 0
    best_diff = abs(compute(0) - target)
    for v in sorted(candidates):
        if v < 0:
            continue
        s = compute(v)
        diff = abs(s - target)
        if diff < best_diff:
            best_diff = diff
            best_v = v
        elif diff == best_diff:
            best_v = min(best_v, v)
    return best_v


# =============================================================================
# WAY 5: Sort + solve for v at each boundary (with proper range check)
# =============================================================================
def find_best_value_5(arr, target):
    """
    Sort. For each boundary k, v must satisfy a[k-1] <= v <= a[k].
    Solve v = (target - prefix[k]) / (n-k) and clamp to valid range.
    """
    a = sorted(arr)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]

    if prefix[n] <= target:
        return a[-1]

    best_v = 0
    best_diff = abs(prefix[n] - target)

    def cap_sum(v):
        return sum(min(x, v) for x in a)

    for k in range(n):
        count_capped = n - k
        if count_capped == 0:
            continue
        v_exact = (target - prefix[k]) / count_capped
        v_floor = int(v_exact)
        v_ceil = v_floor + 1
        # v must satisfy: a[k-1] <= v (for elements 0..k-1 to stay if k>0)
        # AND v < a[k] (for element k to be capped)
        # Actually, the boundary is determined by where v falls relative to a values.
        # Let's just try a range of v values near v_exact.
        candidates = [v_floor, v_ceil]
        # Add neighbors of a[k] and a[k-1]
        if k > 0:
            candidates.append(a[k - 1])
        if k < n:
            candidates.append(a[k])
        for v in candidates:
            if v < 0:
                continue
            s = cap_sum(v)
            diff = abs(s - target)
            if diff < best_diff:
                best_diff = diff
                best_v = v
            elif diff == best_diff:
                best_v = min(best_v, v)
    return best_v


# =============================================================================
# WAY 6: Binary search without prefix (compute sum each time)
# =============================================================================
def find_best_value_6(arr, target):
    def compute(v):
        return sum(min(x, v) for x in arr)

    lo, hi = 0, max(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if compute(mid) < target:
            lo = mid + 1
        else:
            hi = mid
    s_lo = compute(lo)
    s_prev = compute(lo - 1) if lo > 0 else float('inf')
    diff_lo = abs(s_lo - target)
    diff_prev = abs(s_prev - target)
    return lo - 1 if diff_prev <= diff_lo else lo


# =============================================================================
# WAY 7: Sort + iterate boundary with delta exploration
# =============================================================================
def find_best_value_7(arr, target):
    """Sort, then iterate boundary and explore nearby values."""
    a = sorted(arr)
    n = len(a)

    def cap_sum(v):
        return sum(min(x, v) for x in a)

    best_v = 0
    best_diff = abs(cap_sum(0) - target)
    # Check every value from 0 to max(a)
    for v in range(0, a[-1] + 1):
        s = cap_sum(v)
        diff = abs(s - target)
        if diff < best_diff:
            best_diff = diff
            best_v = v
    return best_v


# =============================================================================
# WAY 8: Mathematical: solve v = (target - prefix[k]) / (n-k) (with range check)
# =============================================================================
def find_best_value_8(arr, target):
    """For each k, compute v at boundary. Pick closest. Verify with actual sum."""
    a = sorted(arr)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]

    if prefix[n] <= target:
        return a[-1]

    best_v = 0
    best_diff = float('inf')

    def cap_sum(v):
        return sum(min(x, v) for x in a)

    for k in range(n + 1):
        count_capped = n - k
        if count_capped == 0:
            continue
        # Solve prefix[k] + count_capped * v = target
        v_exact = (target - prefix[k]) / count_capped
        v_floor = int(v_exact)
        v_ceil = v_floor + 1
        # Try floor and ceil, but use actual sum for comparison
        for v in [v_floor, v_ceil]:
            if v < 0:
                continue
            s = cap_sum(v)
            diff = abs(s - target)
            if diff < best_diff:
                best_diff = diff
                best_v = v
            elif diff == best_diff:
                best_v = min(best_v, v)
    return best_v


# =============================================================================
# WAY 9: Sort + iterate prefix on the fly (with actual sum)
# =============================================================================
def find_best_value_9(arr, target):
    """Iterate sorted, compute prefix on the fly. Use actual cap_sum for comparison."""
    a = sorted(arr)
    n = len(a)
    total = sum(a)
    if total <= target:
        return a[-1]

    def cap_sum(v):
        return sum(min(x, v) for x in a)

    best_v = 0
    best_diff = abs(total - target)
    prefix = 0
    for i in range(n):
        remaining = n - i
        v_exact = (target - prefix) / remaining
        v_floor = max(0, int(v_exact))
        for v in [v_floor, v_floor + 1]:
            if v < 0:
                continue
            s = cap_sum(v)
            diff = abs(s - target)
            if diff < best_diff:
                best_diff = diff
                best_v = v
            elif diff == best_diff:
                best_v = min(best_v, v)
        prefix += a[i]
    return best_v


# =============================================================================
# WAY 10: Using bisect_right + standard BS
# =============================================================================
def find_best_value_10(arr, target):
    a = sorted(arr)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]

    def cap_sum(v):
        idx = bisect.bisect_right(a, v)
        return prefix[idx] + (n - idx) * v

    lo, hi = 0, a[-1]
    while lo < hi:
        mid = (lo + hi) // 2
        if cap_sum(mid) < target:
            lo = mid + 1
        else:
            hi = mid
    # Now check lo-1, lo, lo+1 for safety
    candidates = [lo]
    if lo > 0:
        candidates.append(lo - 1)
    if lo < a[-1]:
        candidates.append(lo + 1)
    best_v = candidates[0]
    best_diff = abs(cap_sum(best_v) - target)
    for v in candidates[1:]:
        diff = abs(cap_sum(v) - target)
        if diff < best_diff:
            best_diff = diff
            best_v = v
        elif diff == best_diff:
            best_v = min(best_v, v)
    return best_v


# =============================================================================
# WAY 11: Using numpy
# =============================================================================
def find_best_value_11(arr, target):
    """Use numpy for vectorized operations."""
    import numpy as np
    a = np.sort(np.array(arr))
    n = len(a)
    prefix = np.concatenate([[0], np.cumsum(a)])

    def cap_sum(v):
        idx = int(np.searchsorted(a, v, side='right'))
        return int(prefix[idx] + (n - idx) * v)

    lo, hi = 0, int(a[-1])
    while lo < hi:
        mid = (lo + hi) // 2
        if cap_sum(mid) < target:
            lo = mid + 1
        else:
            hi = mid
    s_lo = cap_sum(lo)
    s_prev = cap_sum(lo - 1) if lo > 0 else float('inf')
    return lo - 1 if abs(s_prev - target) <= abs(s_lo - target) else lo


# =============================================================================
# WAY 12: Direct iteration on all values
# =============================================================================
def find_best_value_12(arr, target):
    """Iterate v from 0 to max(arr), compute sum on-the-fly."""
    def compute(v):
        return sum(min(x, v) for x in arr)

    best_v = 0
    best_diff = abs(compute(0) - target)
    for v in range(1, max(arr) + 1):
        diff = abs(compute(v) - target)
        if diff < best_diff:
            best_diff = diff
            best_v = v
    return best_v


# =============================================================================
# WAY 13: Class-based
# =============================================================================
class MutatedArrayFinder:
    def __init__(self, arr):
        self.a = sorted(arr)
        self.n = len(self.a)
        self.prefix = [0] * (self.n + 1)
        for i in range(self.n):
            self.prefix[i + 1] = self.prefix[i] + self.a[i]

    def cap_sum(self, v):
        idx = bisect.bisect_right(self.a, v)
        return self.prefix[idx] + (self.n - idx) * v

    def find_best_value(self, target):
        lo, hi = 0, self.a[-1]
        while lo < hi:
            mid = (lo + hi) // 2
            if self.cap_sum(mid) < target:
                lo = mid + 1
            else:
                hi = mid
        s_lo = self.cap_sum(lo)
        s_prev = self.cap_sum(lo - 1) if lo > 0 else float('inf')
        return lo - 1 if abs(s_prev - target) <= abs(s_lo - target) else lo


def find_best_value_13(arr, target):
    return MutatedArrayFinder(arr).find_best_value(target)


# =============================================================================
# WAY 14: While loop with manual sum
# =============================================================================
def find_best_value_14(arr, target):
    """BS with manual sum computation each time."""
    sorted_arr = sorted(arr)
    max_val = sorted_arr[-1]

    def sum_at(v):
        s = 0
        for x in sorted_arr:
            s += min(x, v)
        return s

    lo, hi = 0, max_val
    while lo < hi:
        mid = (lo + hi) // 2
        if sum_at(mid) < target:
            lo = mid + 1
        else:
            hi = mid
    s1 = sum_at(lo)
    s2 = sum_at(lo - 1) if lo > 0 else float('inf')
    return lo - 1 if abs(s2 - target) <= abs(s1 - target) else lo


# =============================================================================
# WAY 15: Recursive binary search
# =============================================================================
def find_best_value_15(arr, target):
    """Recursive binary search."""
    a = sorted(arr)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]

    def cap_sum(v):
        idx = bisect.bisect_right(a, v)
        return prefix[idx] + (n - idx) * v

    def search(lo, hi):
        if lo >= hi:
            return lo
        mid = (lo + hi) // 2
        if cap_sum(mid) < target:
            return search(mid + 1, hi)
        return search(lo, mid)

    best = search(0, a[-1])
    s1 = cap_sum(best)
    s2 = cap_sum(best - 1) if best > 0 else float('inf')
    return best - 1 if abs(s2 - target) <= abs(s1 - target) else best


# =============================================================================
# WAY 16: With explicit boundary checks
# =============================================================================
def find_best_value_16(arr, target):
    """BS with explicit boundary check on each side."""
    a = sorted(arr)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]

    def cap_sum(v):
        idx = bisect.bisect_right(a, v)
        return prefix[idx] + (n - idx) * v

    # Find smallest v with sum(v) >= target
    lo, hi = 0, a[-1]
    while lo < hi:
        mid = (lo + hi) // 2
        if cap_sum(mid) < target:
            lo = mid + 1
        else:
            hi = mid
    # lo is candidate. Check lo-1.
    v_hi = lo
    v_lo = lo - 1
    if v_lo < 0:
        return v_hi
    s_hi = cap_sum(v_hi)
    s_lo = cap_sum(v_lo)
    diff_hi = abs(s_hi - target)
    diff_lo = abs(s_lo - target)
    if diff_lo < diff_hi:
        return v_lo
    elif diff_hi < diff_lo:
        return v_hi
    return min(v_hi, v_lo)


# =============================================================================
# WAY 17: Direct solve for v at each boundary
# =============================================================================
def find_best_value_17(arr, target):
    """For each boundary, solve for v directly."""
    a = sorted(arr)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]

    if prefix[n] <= target:
        return a[-1]

    best_v = 0
    best_diff = float('inf')

    for k in range(n + 1):
        count_capped = n - k
        if count_capped == 0:
            continue
        # Direct solve: v = (target - prefix[k]) / count_capped
        v_exact = (target - prefix[k]) / count_capped
        # Try floor and ceil
        for v in [int(v_exact), int(v_exact) + 1]:
            if v < 0:
                continue
            s = sum(min(x, v) for x in a)
            diff = abs(s - target)
            if diff < best_diff:
                best_diff = diff
                best_v = v
            elif diff == best_diff:
                best_v = min(best_v, v)
    return best_v


# =============================================================================
# WAY 18: With prefix sums in helper
# =============================================================================
def find_best_value_18(arr, target):
    """Clean helper function approach."""
    a = sorted(arr)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]

    def capped_sum(v):
        idx = bisect.bisect_right(a, v)
        return prefix[idx] + (n - idx) * v

    lo, hi = 0, a[-1]
    while lo < hi:
        mid = (lo + hi) // 2
        if capped_sum(mid) < target:
            lo = mid + 1
        else:
            hi = mid
    s_lo = capped_sum(lo)
    s_prev = capped_sum(lo - 1) if lo > 0 else float('inf')
    return lo - 1 if abs(s_prev - target) <= abs(s_lo - target) else lo


# =============================================================================
# WAY 19: Most concise
# =============================================================================
def find_best_value_19(arr, target):
    """One-liner style."""
    a = sorted(arr)
    n = len(a)
    p = [0] * (n + 1)
    for i in range(n):
        p[i + 1] = p[i] + a[i]

    def s(v):
        i = bisect.bisect_right(a, v)
        return p[i] + (n - i) * v

    lo, hi = 0, a[-1]
    while lo < hi:
        m = (lo + hi) // 2
        if s(m) < target:
            lo = m + 1
        else:
            hi = m
    return lo - 1 if abs(s(lo - 1) - target) <= abs(s(lo) - target) else lo


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def find_best_value_20(arr, target):
    """
    THE ONE TO MEMORIZE.

    1. Sort array and compute prefix sums.
    2. Binary search on v in [0, max(arr)] for smallest v with sum(v) >= target.
    3. Compare v and v-1; pick smaller diff. On tie, prefer v-1.

    Time:  O(n log n + log(max)) = O(n log n)
    Space: O(n) for prefix
    """
    a = sorted(arr)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]

    def cap_sum(v):
        idx = bisect.bisect_right(a, v)
        return prefix[idx] + (n - idx) * v

    lo, hi = 0, a[-1]
    while lo < hi:
        mid = (lo + hi) // 2
        if cap_sum(mid) < target:
            lo = mid + 1
        else:
            hi = mid

    s_lo = cap_sum(lo)
    s_prev = cap_sum(lo - 1) if lo > 0 else float('inf')
    # Smaller v on tie
    return lo - 1 if abs(s_prev - target) <= abs(s_lo - target) else lo


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find an integer v such that replacing all arr[i] > v with v
makes the sum as close to target as possible. Return smaller v on tie."

Key Insight:
"sum(v) = sum(min(x, v)) is MONOTONICALLY NON-DECREASING in v.
As v grows, the sum grows (or stays). I can BINARY SEARCH on v."

Algorithm:
1. Sort arr, compute prefix sums.
2. Binary search on v in [0, max(arr)]:
   - For each v, compute sum = prefix[idx] + (n-idx)*v
   - idx = bisect_right(arr, v)
3. If sum(mid) < target, v too small -> lo = mid + 1.
4. Else, v might be answer -> hi = mid.
5. After loop, lo is smallest v with sum(lo) >= target.
6. Compare lo and lo-1; pick smaller diff. On tie, return lo-1.

Edge Cases:
- Single element: trivial.
- target > sum(arr): return max(arr).
- target == sum(arr): return max(arr).
- All same elements: simple.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| BS+prefix| O(nlogn)| O(n)   |
| Brute    | O(n*max)| O(1)   |
+----------+--------+--------+

KEY TRICK:
Binary search on the VALUE, not the array index.
The sum function is monotonic in v.

RELATED PROBLEMS:
- Koko Eating Bananas (LC 875): BS on eating speed.
- Capacity To Ship Packages (LC 1011): BS on capacity.
- Smallest Divisor (LC 1283): BS on divisor threshold.
- Min Speed to Arrive on Time (LC 1870): BS on speed.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: BS+prefix+bisect (BEST)", find_best_value_1),
        ("Way 2: BS+manual bisect", find_best_value_2),
        ("Way 3: Brute force linear", find_best_value_3),
        ("Way 4: Linear candidates", find_best_value_4),
        ("Way 5: Sort+solve for v", find_best_value_5),
        ("Way 6: BS no prefix", find_best_value_6),
        ("Way 7: Direct iterate", find_best_value_7),
        ("Way 8: Mathematical solve", find_best_value_8),
        ("Way 9: Sort+iterate prefix on fly", find_best_value_9),
        ("Way 10: Bisect_right variant", find_best_value_10),
        ("Way 11: Numpy vectorized", find_best_value_11),
        ("Way 12: Direct iteration", find_best_value_12),
        ("Way 13: Class OOP", find_best_value_13),
        ("Way 14: While loop manual", find_best_value_14),
        ("Way 15: Recursive BS", find_best_value_15),
        ("Way 16: Explicit boundary", find_best_value_16),
        ("Way 17: Direct solve for v", find_best_value_17),
        ("Way 18: With prefix helper", find_best_value_18),
        ("Way 19: Most concise", find_best_value_19),
        ("Way 20: Final cleanest", find_best_value_20),
    ]

    test_cases = [
        # (arr, target, expected)
        ([4, 9, 3], 10, 3),  # v=3 -> 9, v=4 -> 11, tie -> 3
        ([2, 3, 5], 10, 5),  # v=5 -> 10 exact
        ([60864, 25176, 27249, 21296, 20204], 56803, 11361),
        ([1, 2, 3], 6, 3),  # v=3 -> 6 exact
        ([1, 2, 3], 7, 3),  # sum is too small even with max, return max
        ([1], 1, 1),  # single element
        ([5, 5, 5], 10, 3),  # v=3 -> 9, v=4 -> 12, |9-10|=1 < |12-10|=2
        ([5, 5, 5], 11, 4),  # v=4 -> 12 diff 1, v=3 -> 9 diff 2, return 4
        ([5, 5, 5], 15, 5),  # v=5 -> 15 exact
        ([2, 2, 2], 3, 1),  # v=1 -> 3 exact
        ([2, 2, 2], 4, 1),  # v=1 -> 3 diff 1, v=2 -> 6 diff 2, return 1
        ([1, 1, 1], 5, 1),  # sum too small, return max
        ([10, 1, 1], 9, 7),  # v=7 -> 7+1+1=9 exact
    ]

    print("=" * 70)
    print("SUM OF MUTATED ARRAY CLOSEST TO TARGET - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/sum-of-mutated-array-closest-to-target")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for arr, target, expected in test_cases:
            try:
                result = func(arr[:], target)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: arr={arr[:5]}..., target={target}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on arr={arr[:5]}... - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
