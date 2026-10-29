"""
Two Sum Less Than K
Easy

Given nums[] and k, find max sum of two elements where sum < k.
Return -1 if no such pair exists.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/two-sum-less-than-k

Examples:
    nums=[34,23,1,24,75,33,54,8], k=60 -> 58 (34+24)
    nums=[10,20,30], k=15 -> -1

Constraints:
- 1 <= nums.length <= 100
- 1 <= nums[i] <= 1000
- 1 <= k <= 2000

KEY INSIGHT: Sort. Two-pointer: maximize sum < k.
"""


# =============================================================================
# WAY 1: Sort + two-pointer (BEST - Memorize!)
# =============================================================================
def two_sum_less_than_k_1(nums, k):
    """
    Sort. Two-pointer: maximize sum < k.
    Move right pointer inward to reduce sum, track max.
    """
    a = sorted(nums)
    lo, hi = 0, len(a) - 1
    best = -1
    while lo < hi:
        s = a[lo] + a[hi]
        if s < k:
            best = max(best, s)
            lo += 1  # try larger lo
        else:
            hi -= 1  # need smaller sum
    return best


# =============================================================================
# WAY 2: Sort + two-pointer (verbose)
# =============================================================================
def two_sum_less_than_k_2(nums, k):
    a = sorted(nums)
    n = len(a)
    best = -1
    lo, hi = 0, n - 1
    while lo < hi:
        if a[lo] + a[hi] < k:
            if a[lo] + a[hi] > best:
                best = a[lo] + a[hi]
            lo += 1
        else:
            hi -= 1
    return best


# =============================================================================
# WAY 3: Brute force - all pairs
# =============================================================================
def two_sum_less_than_k_3(nums, k):
    """Check all pairs."""
    best = -1
    n = len(nums)
    for i in range(n):
        for j in range(i + 1, n):
            s = nums[i] + nums[j]
            if s < k and s > best:
                best = s
    return best


# =============================================================================
# WAY 4: Brute force with early termination
# =============================================================================
def two_sum_less_than_k_4(nums, k):
    """Sort, then iterate. Skip if min pair >= k."""
    a = sorted(nums)
    n = len(a)
    best = -1
    for i in range(n):
        for j in range(i + 1, n):
            s = a[i] + a[j]
            if s >= k:
                break  # since sorted, no further pair will work
            if s > best:
                best = s
    return best


# =============================================================================
# WAY 5: Sort + binary search
# =============================================================================
def two_sum_less_than_k_5(nums, k):
    """For each i, find largest j > i with a[i]+a[j] < k."""
    import bisect
    a = sorted(nums)
    n = len(a)
    best = -1
    for i in range(n):
        # Find largest j > i with a[j] < k - a[i]
        target = k - a[i]
        # a is sorted, find rightmost a[j] < target, j > i
        idx = bisect.bisect_left(a, target, i + 1) - 1
        if idx > i:
            s = a[i] + a[idx]
            if s > best:
                best = s
    return best


# =============================================================================
# WAY 6: Sort + bisect_right
# =============================================================================
def two_sum_less_than_k_6(nums, k):
    """Use bisect_right."""
    import bisect
    a = sorted(nums)
    n = len(a)
    best = -1
    for i in range(n):
        target = k - a[i]
        idx = bisect.bisect_left(a, target, i + 1)
        # a[idx-1] is largest < target
        if idx > i + 1:
            s = a[i] + a[idx - 1]
            if s > best:
                best = s
    return best


# =============================================================================
# WAY 7: Hash map
# =============================================================================
def two_sum_less_than_k_7(nums, k):
    """Hash map: for each num, find partner."""
    seen = set()
    best = -1
    for x in nums:
        # We want x + y < k, so y < k - x
        # y must be in seen
        for y in seen:
            if x + y < k and x + y > best:
                best = x + y
        seen.add(x)
    return best


# =============================================================================
# WAY 8: Hash with sorted keys
# =============================================================================
def two_sum_less_than_k_8(nums, k):
    """Sort, then for each i, BS for partner."""
    import bisect
    a = sorted(nums)
    n = len(a)
    best = -1
    for i in range(n):
        # Find j > i with a[j] < k - a[i]
        target = k - a[i]
        # bisect_left returns first idx where a[idx] >= target
        idx = bisect.bisect_left(a, target, i + 1)
        if idx > i + 1:
            s = a[i] + a[idx - 1]
            best = max(best, s)
    return best


# =============================================================================
# WAY 9: Class-based
# =============================================================================
class TwoSumFinder:
    def __init__(self, nums, k):
        self.a = sorted(nums)
        self.k = k
        self.n = len(self.a)

    def find(self):
        lo, hi = 0, self.n - 1
        best = -1
        while lo < hi:
            s = self.a[lo] + self.a[hi]
            if s < self.k:
                best = max(best, s)
                lo += 1
            else:
                hi -= 1
        return best


def two_sum_less_than_k_9(nums, k):
    return TwoSumFinder(nums, k).find()


# =============================================================================
# WAY 10: Sort + iterate descending
# =============================================================================
def two_sum_less_than_k_10(nums, k):
    """Sort descending, iterate to find max."""
    a = sorted(nums, reverse=True)
    n = len(a)
    best = -1
    # Since sorted desc, a[i] + a[j] for i < j is largest when i=0, j=1
    # but we need < k
    for i in range(n):
        for j in range(i + 1, n):
            s = a[i] + a[j]
            if s >= k:
                continue  # try smaller a[j]
            if s > best:
                best = s
            break  # for fixed i, j=1 is largest (since sorted desc)
    return best


# =============================================================================
# WAY 11: Numpy approach
# =============================================================================
def two_sum_less_than_k_11(nums, k):
    """Use numpy for vectorized computation."""
    import numpy as np
    a = np.sort(np.array(nums))
    n = len(a)
    best = -1
    lo, hi = 0, n - 1
    while lo < hi:
        s = int(a[lo] + a[hi])
        if s < k:
            if s > best:
                best = s
            lo += 1
        else:
            hi -= 1
    return best


# =============================================================================
# WAY 12: Recursive
# =============================================================================
def two_sum_less_than_k_12(nums, k):
    """Recursive two-pointer."""
    a = sorted(nums)
    n = len(a)

    def helper(lo, hi, best):
        if lo >= hi:
            return best
        s = a[lo] + a[hi]
        if s < k:
            return helper(lo + 1, hi, max(best, s))
        else:
            return helper(lo, hi - 1, best)

    return helper(0, n - 1, -1)


# =============================================================================
# WAY 13: Generator-based pairs
# =============================================================================
def two_sum_less_than_k_13(nums, k):
    """Generate pairs as tuples."""
    a = sorted(nums)
    n = len(a)
    best = -1
    lo, hi = 0, n - 1
    while lo < hi:
        s = a[lo] + a[hi]
        if s < k:
            best = max(best, s)
            lo += 1
        else:
            hi -= 1
    return best


# =============================================================================
# WAY 14: Using enumerate
# =============================================================================
def two_sum_less_than_k_14(nums, k):
    """Use enumerate."""
    a = sorted(nums)
    best = -1
    n = len(a)
    for i, x in enumerate(a):
        # Find largest j > i with x + a[j] < k
        import bisect
        target = k - x
        idx = bisect.bisect_left(a, target, i + 1)
        if idx > i + 1:
            s = x + a[idx - 1]
            if s > best:
                best = s
    return best


# =============================================================================
# WAY 15: Itertools combinations
# =============================================================================
def two_sum_less_than_k_15(nums, k):
    """Use itertools.combinations."""
    from itertools import combinations
    best = -1
    for x, y in combinations(sorted(nums), 2):
        s = x + y
        if s < k and s > best:
            best = s
    return best


# =============================================================================
# WAY 16: With heap
# =============================================================================
def two_sum_less_than_k_16(nums, k):
    """Use min-heap for next candidate."""
    import heapq
    a = sorted(nums)
    n = len(a)
    # Generate pairs (sum, lo, hi) where sum is smallest first
    # But we want max sum < k
    # Strategy: iterate i, for each find largest valid j
    best = -1
    for i in range(n):
        import bisect
        target = k - a[i]
        idx = bisect.bisect_left(a, target, i + 1)
        if idx > i + 1:
            best = max(best, a[i] + a[idx - 1])
    return best


# =============================================================================
# WAY 17: With manual BS
# =============================================================================
def two_sum_less_than_k_17(nums, k):
    """Manual binary search."""
    a = sorted(nums)
    n = len(a)
    best = -1
    for i in range(n):
        # Find largest j > i with a[j] < k - a[i]
        target = k - a[i]
        lo, hi = i + 1, n - 1
        result = i  # means no valid j found
        while lo <= hi:
            mid = (lo + hi) // 2
            if a[mid] < target:
                result = mid
                lo = mid + 1
            else:
                hi = mid - 1
        if result > i:
            s = a[i] + a[result]
            if s > best:
                best = s
    return best


# =============================================================================
# WAY 18: Sort + iterate with index tracking
# =============================================================================
def two_sum_less_than_k_18(nums, k):
    """Use index tracking."""
    a = sorted(nums)
    best = -1
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            if a[i] + a[j] >= k:
                break
            best = max(best, a[i] + a[j])
    return best


# =============================================================================
# WAY 19: One-liner style
# =============================================================================
def two_sum_less_than_k_19(nums, k):
    """Concise."""
    a = sorted(nums)
    l, r = 0, len(a) - 1
    best = -1
    while l < r:
        if (s := a[l] + a[r]) < k:
            best = max(best, s)
            l += 1
        else:
            r -= 1
    return best


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def two_sum_less_than_k_20(nums, k):
    """
    THE ONE TO MEMORIZE.

    1. Sort nums.
    2. Two-pointer: lo=0, hi=n-1.
    3. If a[lo] + a[hi] < k: best = max(best, sum), lo += 1.
    4. Else: hi -= 1.
    5. Return best (-1 if no valid pair).

    Time:  O(n log n)
    Space: O(1) extra
    """
    a = sorted(nums)
    lo, hi = 0, len(a) - 1
    best = -1
    while lo < hi:
        s = a[lo] + a[hi]
        if s < k:
            best = max(best, s)
            lo += 1
        else:
            hi -= 1
    return best


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the maximum sum of two elements where sum < k."

Key Insight:
"Sort the array. Use two-pointer from both ends.
- If sum < k: this is a candidate, try larger lo to find bigger sum.
- If sum >= k: need smaller sum, decrease hi."

Algorithm:
1. Sort nums.
2. lo = 0, hi = n-1, best = -1.
3. While lo < hi:
   - s = a[lo] + a[hi]
   - If s < k: best = max(best, s); lo += 1 (try bigger sum)
   - Else: hi -= 1 (need smaller sum)
4. Return best.

Edge Cases:
- No valid pair: return -1.
- All elements same: handled.
- k very small (e.g., 1): return -1.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| 2-ptr    | O(nlogn)| O(1)   |
| Brute    | O(n^2) | O(1)   |
+----------+--------+--------+

KEY TRICK:
Two-pointer exploits sorted structure: increase lo for bigger sum,
decrease hi for smaller sum.

RELATED PROBLEMS:
- Two Sum (LC 1): classic with hash map.
- Two Sum II (LC 167): sorted array, two-pointer.
- 3Sum (LC 15): three-sum variant.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort+2ptr (BEST)", two_sum_less_than_k_1),
        ("Way 2: 2ptr verbose", two_sum_less_than_k_2),
        ("Way 3: Brute force", two_sum_less_than_k_3),
        ("Way 4: Brute early term", two_sum_less_than_k_4),
        ("Way 5: Sort+BS", two_sum_less_than_k_5),
        ("Way 6: Sort+bisect_right", two_sum_less_than_k_6),
        ("Way 7: Hash map", two_sum_less_than_k_7),
        ("Way 8: Hash+sort", two_sum_less_than_k_8),
        ("Way 9: Class OOP", two_sum_less_than_k_9),
        ("Way 10: Sort desc", two_sum_less_than_k_10),
        ("Way 11: Numpy", two_sum_less_than_k_11),
        ("Way 12: Recursive", two_sum_less_than_k_12),
        ("Way 13: Generator", two_sum_less_than_k_13),
        ("Way 14: Enumerate+BS", two_sum_less_than_k_14),
        ("Way 15: Itertools", two_sum_less_than_k_15),
        ("Way 16: With heap", two_sum_less_than_k_16),
        ("Way 17: Manual BS", two_sum_less_than_k_17),
        ("Way 18: Index tracking", two_sum_less_than_k_18),
        ("Way 19: One-liner", two_sum_less_than_k_19),
        ("Way 20: Final cleanest", two_sum_less_than_k_20),
    ]

    test_cases = [
        # (nums, k, expected)
        ([34, 23, 1, 24, 75, 33, 54, 8], 60, 58),
        ([10, 20, 30], 15, -1),
        ([1, 2, 3], 6, 5),  # 2+3=5
        ([1, 2, 3], 5, 4),  # 1+3=4
        ([1, 2, 3], 100, 5),  # 2+3=5
        ([5, 5, 5], 10, -1),  # 5+5=10 not <10
        ([5, 5, 5], 11, 10),  # 5+5=10
        ([1], 5, -1),  # single element
        ([1, 2], 5, 3),  # 1+2=3
        ([1, 2], 3, -1),  # 1+2=3 not <3
        ([1, 2, 3, 4, 5], 9, 8),  # 3+5=8 or 4+5=9 not, so 8
        ([1, 2, 3, 4, 5], 8, 7),  # 3+4=7
    ]

    print("=" * 70)
    print("TWO SUM LESS THAN K - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/two-sum-less-than-k")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums, k, expected in test_cases:
            try:
                result = func(nums[:], k)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: nums={nums}, k={k}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)