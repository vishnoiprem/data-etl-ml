"""
Valid Triangle Number
Medium | 30 min

Given an integer array nums, return the number of triplets chosen from
the array that can make triangles if we take them as side lengths of a
triangle.

Triangle inequality: for sorted sides a <= b <= c, valid iff a + b > c.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/valid-triangle-number

Examples:
    nums=[2,2,3,4] -> 3
    # Triplets: (2,2,3), (2,3,4), (2,2,4)... let's check
    # Sort: [2,2,3,4]
    # i=2 (c=3): lo=0, hi=1: 2+2=4>3 ✓, count+=1. lo=1. Exit.
    # i=3 (c=4): lo=0, hi=2: 2+2=4 not>4. lo=1. 2+3=5>4 ✓, count+=1. lo=2. Exit.
    # Total: 3
    nums=[4,2,3,4] -> 4

Constraints:
- 1 <= nums.length <= 1000
- 0 <= nums[i] <= 1000

KEY INSIGHT: Sort. For each i (longest side c), use two-pointer:
if nums[lo] + nums[hi] > c: all pairs (lo..hi-1, hi) are valid -> count += hi - lo, hi--
else: lo++.
"""


# =============================================================================
# WAY 1: Sort + two-pointer (BEST - Memorize!)
# =============================================================================
def triangle_number_1(nums):
    """
    Sort. For each i as longest side, two-pointer counts pairs (lo, hi)
    with nums[lo] + nums[hi] > nums[i].
    """
    a = sorted(nums)
    n = len(a)
    count = 0
    for i in range(2, n):
        lo, hi = 0, i - 1
        while lo < hi:
            if a[lo] + a[hi] > a[i]:
                # All pairs (lo..hi-1, hi) work since a is sorted
                count += hi - lo
                hi -= 1
            else:
                lo += 1
    return count


# =============================================================================
# WAY 2: Sort + two-pointer (verbose)
# =============================================================================
def triangle_number_2(nums):
    a = sorted(nums)
    n = len(a)
    count = 0
    for i in range(n):
        lo, hi = 0, i - 1
        while lo < hi:
            s = a[lo] + a[hi]
            if s > a[i]:
                count += hi - lo
                hi -= 1
            else:
                lo += 1
    return count


# =============================================================================
# WAY 3: Brute force - all triplets
# =============================================================================
def triangle_number_3(nums):
    """Check all i < j < k combinations."""
    n = len(nums)
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                a, b, c = nums[i], nums[j], nums[k]
                # Check triangle inequality on all permutations
                if a + b > c and a + c > b and b + c > a:
                    count += 1
    return count


# =============================================================================
# WAY 4: Brute force with sort
# =============================================================================
def triangle_number_4(nums):
    """Sort, then check all triplets (only need to check one direction)."""
    a = sorted(nums)
    n = len(a)
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                if a[i] + a[j] > a[k]:
                    count += 1
    return count


# =============================================================================
# WAY 5: Sort + binary search
# =============================================================================
def triangle_number_5(nums):
    """
    Sort. For each (i, j) with i < j, find largest k > j with
    nums[i] + nums[j] > nums[k] using binary search.
    """
    import bisect
    a = sorted(nums)
    n = len(a)
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            # Need a[k] < a[i] + a[j], k > j
            target = a[i] + a[j]
            idx = bisect.bisect_left(a, target, j + 1)
            # a[idx-1] is largest < target (or idx-1 == j if none valid)
            count += max(0, idx - j - 1)
    return count


# =============================================================================
# WAY 6: Sort + bisect_right
# =============================================================================
def triangle_number_6(nums):
    """Sort + bisect_right to find largest valid k."""
    import bisect
    a = sorted(nums)
    n = len(a)
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            target = a[i] + a[j]
            # We want largest k > j where a[k] < target
            # bisect_left(a, target, j+1) returns first idx with a[idx] >= target
            idx = bisect.bisect_left(a, target, j + 1)
            # All a[j+1..idx-1] are < target and form valid triangles
            if idx > j + 1:
                count += idx - j - 1
    return count


# =============================================================================
# WAY 7: Sort + fix largest + iterate k
# =============================================================================
def triangle_number_7(nums):
    """Sort, fix largest c = nums[i]. For each k from i-1 down, count
    valid j's (j < k) with a[j] + a[k] > c."""
    import bisect
    a = sorted(nums)
    n = len(a)
    count = 0
    for i in range(2, n):
        # Need a[j] + a[k] > a[i], i.e., a[j] > a[i] - a[k]
        for k in range(i - 1, 0, -1):
            # need a[j] > a[i] - a[k]
            target = a[i] - a[k]
            # Find first j where a[j] > target (strict)
            j = bisect.bisect_right(a, target, 0, k)
            # Valid j's: j, j+1, ..., k-1 (all >= j, none equal k)
            if k > j:
                count += k - j
    return count


# =============================================================================
# WAY 8: With helper function
# =============================================================================
def triangle_number_8(nums):
    """Use helper function for two-pointer counting."""
    a = sorted(nums)
    n = len(a)

    def count_pairs_for_target(c_idx):
        lo, hi = 0, c_idx - 1
        cnt = 0
        while lo < hi:
            if a[lo] + a[hi] > a[c_idx]:
                cnt += hi - lo
                hi -= 1
            else:
                lo += 1
        return cnt

    count = 0
    for i in range(2, n):
        count += count_pairs_for_target(i)
    return count


# =============================================================================
# WAY 9: Recursive two-pointer
# =============================================================================
def triangle_number_9(nums):
    """Recursive approach."""
    a = sorted(nums)
    n = len(a)
    count = [0]

    def helper(lo, hi, c):
        if lo >= hi:
            return
        if a[lo] + a[hi] > c:
            count[0] += hi - lo
            helper(lo, hi - 1, c)
        else:
            helper(lo + 1, hi, c)

    for i in range(2, n):
        helper(0, i - 1, a[i])

    return count[0]


# =============================================================================
# WAY 10: Class-based
# =============================================================================
class TriangleCounter:
    def __init__(self, nums):
        self.a = sorted(nums)
        self.n = len(self.a)

    def count_pairs(self, c_idx):
        lo, hi = 0, c_idx - 1
        cnt = 0
        while lo < hi:
            if self.a[lo] + self.a[hi] > self.a[c_idx]:
                cnt += hi - lo
                hi -= 1
            else:
                lo += 1
        return cnt

    def count(self):
        total = 0
        for i in range(2, self.n):
            total += self.count_pairs(i)
        return total


def triangle_number_10(nums):
    return TriangleCounter(nums).count()


# =============================================================================
# WAY 11: Sort + itertools.combinations
# =============================================================================
def triangle_number_11(nums):
    """Use itertools.combinations to enumerate triplets."""
    from itertools import combinations
    a = sorted(nums)
    count = 0
    for i, j, k in combinations(range(len(a)), 3):
        if a[i] + a[j] > a[k]:
            count += 1
    return count


# =============================================================================
# WAY 12: Sort + numpy
# =============================================================================
def triangle_number_12(nums):
    """Vectorized with numpy."""
    import numpy as np
    a = np.sort(np.array(nums))
    n = len(a)
    count = 0
    for i in range(n):
        js = np.arange(i + 1, n)
        sums = a[i] + a[js]
        ks = np.searchsorted(a, sums, side='left')
        # Valid k's are (j+1)..(ks-1). Count = max(0, ks - (j+1)).
        valid = np.maximum(0, ks - (js + 1))
        count += int(valid.sum())
    return count


# =============================================================================
# WAY 13: Sort + manual binary search
# =============================================================================
def triangle_number_13(nums):
    """Sort, manual binary search for each (i, j)."""
    a = sorted(nums)
    n = len(a)
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            target = a[i] + a[j]
            # Find largest k > j with a[k] < target
            lo, hi = j + 1, n - 1
            result = j  # means no valid k
            while lo <= hi:
                mid = (lo + hi) // 2
                if a[mid] < target:
                    result = mid
                    lo = mid + 1
                else:
                    hi = mid - 1
            count += max(0, result - j)
    return count


# =============================================================================
# WAY 14: One-liner style
# =============================================================================
def triangle_number_14(nums):
    """Concise two-pointer version."""
    a = sorted(nums)
    n = len(a)
    count = 0
    for i in range(2, n):
        l, r = 0, i - 1
        while l < r:
            if a[l] + a[r] > a[i]:
                count += r - l
                r -= 1
            else:
                l += 1
    return count


# =============================================================================
# WAY 15: Using Counter / hashing (slow but interesting)
# =============================================================================
def triangle_number_15(nums):
    """Count occurrences, then enumerate."""
    from collections import Counter
    cnt = Counter(nums)
    vals = sorted(cnt.keys())
    n = len(vals)
    count = 0
    for i in range(n):
        for j in range(i, n):
            c = vals[i] + vals[j]  # need k < c
            # Find largest idx where vals[idx] < c
            import bisect
            idx = bisect.bisect_left(vals, c)
            for k in range(j, idx):
                ki = vals[k]
                # Count triplet (vals[i], vals[j], ki)
                if i == j == k:
                    n_triplets = cnt[vals[i]] * (cnt[vals[i]] - 1) * (cnt[vals[i]] - 2) // 6
                elif i == j:
                    n_triplets = cnt[vals[i]] * (cnt[vals[i]] - 1) // 2 * cnt[ki]
                elif i == k:
                    n_triplets = cnt[vals[i]] * (cnt[vals[j]]) * (cnt[vals[i]] - 1) // 2
                elif j == k:
                    n_triplets = cnt[vals[i]] * cnt[vals[j]] * (cnt[vals[j]] - 1) // 2
                else:
                    n_triplets = cnt[vals[i]] * cnt[vals[j]] * cnt[ki]
                count += n_triplets
    return count


# =============================================================================
# WAY 16: Sort + reverse two-pointer
# =============================================================================
def triangle_number_16(nums):
    """Variant: iterate longest side from end."""
    a = sorted(nums)
    n = len(a)
    count = 0
    for i in range(n - 1, 1, -1):
        lo, hi = 0, i - 1
        while lo < hi:
            if a[lo] + a[hi] > a[i]:
                count += hi - lo
                hi -= 1
            else:
                lo += 1
    return count


# =============================================================================
# WAY 17: Sort + early break
# =============================================================================
def triangle_number_17(nums):
    """With early break when sum too small."""
    a = sorted(nums)
    n = len(a)
    count = 0
    for i in range(2, n):
        lo, hi = 0, i - 1
        while lo < hi:
            if a[lo] + a[hi] > a[i]:
                count += hi - lo
                hi -= 1
            else:
                lo += 1
    return count


# =============================================================================
# WAY 18: Generator-style
# =============================================================================
def triangle_number_18(nums):
    """Use generator to yield (lo, hi, i) triplets and count valid."""
    a = sorted(nums)
    n = len(a)
    count = 0

    def gen_pairs(i):
        for hi in range(i - 1, 0, -1):
            for lo in range(hi):
                yield lo, hi, i

    for i in range(2, n):
        for lo, hi, ii in gen_pairs(i):
            if a[lo] + a[hi] > a[ii]:
                count += 1
    return count


# =============================================================================
# WAY 19: Using functools / memoization
# =============================================================================
def triangle_number_19(nums):
    """Sort, with memoization on (i, j) pairs."""
    from functools import lru_cache
    a = sorted(nums)
    n = len(a)

    @lru_cache(maxsize=None)
    def count_for(i):
        """Count pairs (lo, hi) with lo < hi < i and a[lo] + a[hi] > a[i]."""
        if i < 2:
            return 0
        lo, hi = 0, i - 1
        cnt = 0
        while lo < hi:
            if a[lo] + a[hi] > a[i]:
                cnt += hi - lo
                hi -= 1
            else:
                lo += 1
        return cnt

    total = 0
    for i in range(2, n):
        total += count_for(i)
    return total


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def triangle_number_20(nums):
    """
    THE ONE TO MEMORIZE.

    1. Sort nums.
    2. For each i (longest side):
       - lo = 0, hi = i - 1.
       - If a[lo] + a[hi] > a[i]: all pairs (lo..hi-1, hi) valid -> count += hi - lo, hi--.
       - Else: lo++.
    3. Return count.

    Time:  O(n^2)
    Space: O(1) extra (after sort)
    """
    a = sorted(nums)
    n = len(a)
    count = 0
    for i in range(2, n):
        lo, hi = 0, i - 1
        while lo < hi:
            if a[lo] + a[hi] > a[i]:
                count += hi - lo
                hi -= 1
            else:
                lo += 1
    return count


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to count triplets that can form valid triangles. For sorted
sides a <= b <= c, the only check needed is a + b > c."

Key Insight:
"Sort the array. For each index i (as longest side c), use two-pointer
to count pairs (lo, hi) with lo < hi < i and a[lo] + a[hi] > a[i].
If a[lo] + a[hi] > a[i], then ALL pairs (lo..hi-1, hi) work because
a[lo'] >= a[lo] for lo' > lo. So count += hi - lo and decrement hi."

Algorithm:
1. Sort nums.
2. For i from 2 to n-1:
   - lo = 0, hi = i - 1.
   - While lo < hi:
     - If a[lo] + a[hi] > a[i]: count += hi - lo; hi -= 1.
     - Else: lo += 1.
3. Return count.

Edge Cases:
- All zeros: return 0 (no a+b > c with strict inequality).
- Single/two elements: return 0.
- All same: depends on whether a + a > a (i.e., a > 0).

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| 2-ptr    | O(n^2) | O(1)   |
| BS       | O(n^2l | O(1)   |
|          | ogn)   |        |
| Brute    | O(n^3) | O(1)   |
+----------+--------+--------+

KEY TRICK:
The "if a[lo] + a[hi] > c, count += hi - lo" trick. Since array is
sorted, increasing lo only INCREASES a[lo] (sum gets bigger), so all
pairs (lo, hi), (lo+1, hi), ..., (hi-1, hi) are valid.

RELATED PROBLEMS:
- 3Sum (LC 15): three-sum equals zero.
- 3Sum Smaller (LC 259): count 3-sums with sum < target. SAME trick.
- Container With Most Water (LC 11): two-pointer.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort+2ptr (BEST)", triangle_number_1),
        ("Way 2: 2ptr verbose", triangle_number_2),
        ("Way 3: Brute force", triangle_number_3),
        ("Way 4: Brute sorted", triangle_number_4),
        ("Way 5: Sort+BS", triangle_number_5),
        ("Way 6: Sort+bisect_right", triangle_number_6),
        ("Way 7: Fix largest+iterate", triangle_number_7),
        ("Way 8: Helper fn", triangle_number_8),
        ("Way 9: Recursive", triangle_number_9),
        ("Way 10: Class OOP", triangle_number_10),
        ("Way 11: Itertools", triangle_number_11),
        ("Way 12: Numpy", triangle_number_12),
        ("Way 13: Manual BS", triangle_number_13),
        ("Way 14: One-liner", triangle_number_14),
        ("Way 15: Counter/hashing", triangle_number_15),
        ("Way 16: Reverse 2ptr", triangle_number_16),
        ("Way 17: Early break", triangle_number_17),
        ("Way 18: Generator", triangle_number_18),
        ("Way 19: LRU cache", triangle_number_19),
        ("Way 20: Final cleanest", triangle_number_20),
    ]

    test_cases = [
        # (nums, expected)
        ([2, 2, 3, 4], 3),
        ([4, 2, 3, 4], 4),
        ([0, 0, 0], 0),  # 0+0 not > 0
        ([1, 1, 1], 1),  # 1+1>1
        ([1, 2, 3], 0),  # 1+2=3 not >3
        ([2, 2, 2], 1),
        ([3, 4, 5], 1),
        ([1], 0),  # single
        ([1, 2], 0),  # two
        ([1, 2, 3, 4, 5], 3),  # (1,2,3),(2,3,4),(3,4,5) wait 1+2=3 not>3. So 2: (2,3,4),(3,4,5)
        # Brute force: [3,3,4,4,5,5] has 6C3=20 triplets, all valid (3+3=6>5).
        ([3, 3, 4, 4, 5, 5], 20),
        # [4,2,3,4] sort=[2,3,4,4]. Triplets: (2,3,4)x2 since 2 fours → (2,3,4): 2*2=2 pick (3,4) wait
        # (2,3,4) first 4: 2+3=5>4 ✓. (2,3,4) second 4: 2+3=5>4 ✓. (2,4,4): 2+4=6>4 ✓. (3,4,4): 3+4=7>4 ✓. Total 4.
        ([4, 2, 3, 4], 4),
        # Recount [1,2,3,4,5]:
        # i=2 (c=3): lo=0,hi=1. 1+2=3 not>3. lo=1. Exit. adds 0.
        # i=3 (c=4): lo=0,hi=2. 1+3=4 not>4. lo=1. 2+3=5>4 ✓, count+=1. hi=1. Exit. adds 1.
        # i=4 (c=5): lo=0,hi=3. 1+4=5 not>5. lo=1. 2+4=6>5 ✓, count+=2. hi=2. 2+3=5 not>5. lo=2. Exit. adds 2.
        # Total: 3.
        ([1, 2, 3, 4, 5], 3),
        ([0, 1, 1, 1], 1),  # only (1,1,1) works; (0,1,1) needs 0+1>1 false
        ([2, 2, 2, 2], 4),  # all 4C3=4 triplets, 2+2>2 ✓
        ([5, 5, 5, 5, 5], 10),  # 5C3=10
        ([10, 11, 12, 13, 14, 15], 20),  # 6C3=20, all valid
    ]

    print("=" * 70)
    print("VALID TRIANGLE NUMBER - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/valid-triangle-number")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums, expected in test_cases:
            try:
                result = func(nums[:])
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: nums={nums}, expected={expected}, got={result}")
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
