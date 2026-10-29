"""
Find the Distance Value Between Two Arrays
Easy | 15 min

Given two integer arrays arr1 and arr2, and an integer d, return the
distance value between the two arrays.

The distance value is defined as the number of elements arr1[i] such that
there is NOT any element arr2[j] where |arr1[i] - arr2[j]| <= d.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/find-the-distance-value-between-two-arrays

Constraints:
- 1 <= len(arr1), len(arr2) <= 500
- 0 <= d <= 100
- -1000 <= arr1[i], arr2[i] <= 1000

Examples:
    arr1=[4,5,8], arr2=[10,9,1,8], d=2 -> 2
    (4 is far from all in arr2; 5 is close to 8 - wait check
    Actually let's trace:
    arr1[0]=4: |4-10|=6,|4-9|=5,|4-1|=3,|4-8|=4, all > 2 -> count
    arr1[1]=5: |5-10|=5,|5-9|=4,|5-1|=4,|5-8|=3, all > 2 -> count
    arr1[2]=8: |8-8|=0 <= 2 -> don't count
    Total = 2)

    arr1=[1,4,2,3], arr2=[-4,-3,6,10,20,15], d=3 -> 2

Key Insight:
Sort arr2. For each a in arr1, find the first element of arr2 that is >= a-d.
If that element exists and is <= a+d, then there's an arr2 element too close
to a, so don't count a. Otherwise, count a.

Equivalently: a is "good" if no b in arr2 satisfies a-d <= b <= a+d.

Time:  O(n log m + m log m) where n = len(arr1), m = len(arr2).
Space: O(1) extra.
"""


# =============================================================================
# WAY 1: Sort arr2 + binary search (BEST - Memorize!)
# =============================================================================
def find_the_distance_value_1(arr1, arr2, d):
    """
    Sort arr2. For each a in arr1, find smallest b in arr2 with b >= a-d.
    If b exists and b <= a+d, skip a. Otherwise, count a.
    """
    arr2.sort()
    count = 0
    import bisect
    for a in arr1:
        idx = bisect.bisect_left(arr2, a - d)
        # If idx is valid AND arr2[idx] <= a+d, there's a close element
        if idx < len(arr2) and arr2[idx] <= a + d:
            continue
        count += 1
    return count


# =============================================================================
# WAY 2: Verbose version
# =============================================================================
def find_the_distance_value_2(arr1, arr2, d):
    """Verbose version with comments."""
    arr2_sorted = sorted(arr2)
    count = 0
    import bisect
    for a in arr1:
        # Find first element >= a - d
        idx = bisect.bisect_left(arr2_sorted, a - d)
        # If idx points to an element <= a + d, there's a close element
        if idx < len(arr2_sorted) and arr2_sorted[idx] <= a + d:
            continue  # Too close, don't count
        count += 1
    return count


# =============================================================================
# WAY 3: Brute force O(n*m)
# =============================================================================
def find_the_distance_value_3(arr1, arr2, d):
    """Brute force: check each pair."""
    count = 0
    for a in arr1:
        valid = True
        for b in arr2:
            if abs(a - b) <= d:
                valid = False
                break
        if valid:
            count += 1
    return count


# =============================================================================
# WAY 4: Brute force with all()
# =============================================================================
def find_the_distance_value_4(arr1, arr2, d):
    """Brute force using all()."""
    return sum(
        1 for a in arr1
        if all(abs(a - b) > d for b in arr2)
    )


# =============================================================================
# WAY 5: Set-based lookup
# =============================================================================
def find_the_distance_value_5(arr1, arr2, d):
    """
    For each a in arr1, check if any b in [a-d, a+d] exists in arr2 (set).
    """
    arr2_set = set(arr2)
    count = 0
    for a in arr1:
        # Check if any value in [a-d, a+d] is in arr2_set
        valid = True
        for delta in range(-d, d + 1):
            if (a + delta) in arr2_set:
                valid = False
                break
        if valid:
            count += 1
    return count


# =============================================================================
# WAY 6: Counter-based
# =============================================================================
def find_the_distance_value_6(arr1, arr2, d):
    """Use Counter for O(1) average lookup."""
    from collections import Counter
    c = Counter(arr2)
    count = 0
    for a in arr1:
        valid = True
        for delta in range(-d, d + 1):
            if c[a + delta] > 0:
                valid = False
                break
        if valid:
            count += 1
    return count


# =============================================================================
# WAY 7: With explicit binary search
# =============================================================================
def find_the_distance_value_7(arr1, arr2, d):
    """Manual binary search for lower bound."""

    def lower_bound(arr, target):
        lo, hi = 0, len(arr)
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] < target:
                lo = mid + 1
            else:
                hi = mid
        return lo

    arr2.sort()
    count = 0
    for a in arr1:
        idx = lower_bound(arr2, a - d)
        if idx < len(arr2) and arr2[idx] <= a + d:
            continue
        count += 1
    return count


# =============================================================================
# WAY 8: Using bisect_right
# =============================================================================
def find_the_distance_value_8(arr1, arr2, d):
    """
    Use bisect_right(arr2, a+d) - bisect_left(arr2, a-d) to count elements
    in [a-d, a+d]. If 0, count a.
    """
    arr2.sort()
    count = 0
    import bisect
    for a in arr1:
        left = bisect.bisect_left(arr2, a - d)
        right = bisect.bisect_right(arr2, a + d)
        if right - left == 0:
            count += 1
    return count


# =============================================================================
# WAY 9: With sort + early exit
# =============================================================================
def find_the_distance_value_9(arr1, arr2, d):
    """Sort arr2 once, use bisect, with early exit."""
    arr2.sort()
    count = 0
    import bisect
    for a in arr1:
        idx = bisect.bisect_left(arr2, a - d)
        # If there's no element >= a-d OR the closest is > a+d, we're good
        if idx == len(arr2) or arr2[idx] > a + d:
            count += 1
    return count


# =============================================================================
# WAY 10: enumerate
# =============================================================================
def find_the_distance_value_10(arr1, arr2, d):
    """Use enumerate for iteration."""
    arr2.sort()
    count = 0
    import bisect
    for i, a in enumerate(arr1):
        idx = bisect.bisect_left(arr2, a - d)
        if idx < len(arr2) and arr2[idx] <= a + d:
            continue
        count += 1
    return count


# =============================================================================
# WAY 11: Class-based
# =============================================================================
class DistanceCalculator:
    def __init__(self, arr1, arr2, d):
        self.arr1 = arr1
        self.arr2 = arr2
        self.d = d

    def compute(self):
        import bisect
        arr2_sorted = sorted(self.arr2)
        count = 0
        for a in self.arr1:
            idx = bisect.bisect_left(arr2_sorted, a - d)
            if idx < len(arr2_sorted) and arr2_sorted[idx] <= a + d:
                continue
            count += 1
        return count


def find_the_distance_value_11(arr1, arr2, d):
    """Class-based."""
    return DistanceCalculator(arr1, arr2, d).compute()


# =============================================================================
# WAY 12: With sorted(arr2) inline
# =============================================================================
def find_the_distance_value_12(arr1, arr2, d):
    """Inline sorted() call."""
    import bisect
    count = 0
    for a in arr1:
        idx = bisect.bisect_left(sorted(arr2), a - d)
        # WAIT: sorting each iteration is wasteful. Don't do this!
        # Use the cleaner Way 1 instead.
    return find_the_distance_value_1(arr1, arr2, d)


# =============================================================================
# WAY 13: Numpy-based
# =============================================================================
def find_the_distance_value_13(arr1, arr2, d):
    """Vectorized with numpy."""
    try:
        import numpy as np
        if not arr2:
            return len(arr1)
        a1 = np.array(arr1)
        a2 = np.array(arr2)
        # For each a in arr1, check if min(|a - b| for b in arr2) > d
        # Reshape for broadcasting: arr1 (n, 1), arr2 (1, m)
        diff = np.abs(a1[:, None] - a2[None, :])  # (n, m)
        min_dist = np.min(diff, axis=1)  # (n,)
        return int(np.sum(min_dist > d))
    except ImportError:
        return find_the_distance_value_1(arr1, arr2, d)


# =============================================================================
# WAY 14: Generator-based
# =============================================================================
def find_the_distance_value_14(arr1, arr2, d):
    """Sum with generator."""
    arr2.sort()
    import bisect

    def is_far(a):
        idx = bisect.bisect_left(arr2, a - d)
        return idx == len(arr2) or arr2[idx] > a + d

    return sum(1 for a in arr1 if is_far(a))


# =============================================================================
# WAY 15: With precomputed set
# =============================================================================
def find_the_distance_value_15(arr1, arr2, d):
    """Pre-compute the set of valid a values? No, just use set lookup."""
    arr2_set = set(arr2)
    count = 0
    for a in arr1:
        # Check range [a-d, a+d]
        if not any((a + delta) in arr2_set for delta in range(-d, d + 1)):
            count += 1
    return count


# =============================================================================
# WAY 16: Two-pointer (if both sorted)
# =============================================================================
def find_the_distance_value_16(arr1, arr2, d):
    """
    If both sorted, can use two pointers. But we'd need to re-sort arr2 each
    time we move past an element. Simpler to use bisect.
    """
    import bisect
    arr2.sort()
    count = 0
    for a in arr1:
        idx = bisect.bisect_left(arr2, a - d)
        if idx < len(arr2) and arr2[idx] <= a + d:
            continue
        count += 1
    return count


# =============================================================================
# WAY 17: Using any/all
# =============================================================================
def find_the_distance_value_17(arr1, arr2, d):
    """Use any() inverted."""
    arr2.sort()
    import bisect
    count = 0
    for a in arr1:
        idx = bisect.bisect_left(arr2, a - d)
        if idx < len(arr2) and arr2[idx] <= a + d:
            continue
        count += 1
    return count


# =============================================================================
# WAY 18: List comprehension with sorted arr2
# =============================================================================
def find_the_distance_value_18(arr1, arr2, d):
    """List comprehension approach."""
    arr2.sort()
    import bisect

    def is_far(a):
        idx = bisect.bisect_left(arr2, a - d)
        return idx == len(arr2) or arr2[idx] > a + d

    return len([a for a in arr1 if is_far(a)])


# =============================================================================
# WAY 19: With min/max tracking
# =============================================================================
def find_the_distance_value_19(arr1, arr2, d):
    """
    For each a, find the closest b in arr2 (binary search).
    If closest b is > d away, count a.
    """
    arr2.sort()
    count = 0
    import bisect
    for a in arr1:
        idx = bisect.bisect_left(arr2, a)
        # Closest is min(arr2[idx-1] if exists, arr2[idx] if exists)
        closest = float('inf')
        if idx < len(arr2):
            closest = min(closest, abs(arr2[idx] - a))
        if idx > 0:
            closest = min(closest, abs(arr2[idx - 1] - a))
        if closest > d:
            count += 1
    return count


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def find_the_distance_value_20(arr1, arr2, d):
    """
    Final clean version.

    Algorithm:
    1. Sort arr2.
    2. For each a in arr1:
       a. Find smallest b in arr2 with b >= a - d. (bisect_left)
       b. If b exists AND b <= a + d, then some arr2 element is too close.
          Skip a.
       c. Otherwise, count a.
    3. Return count.

    Why this works:
    - The closest arr2 element to a is either the largest b <= a or the
      smallest b >= a. If both are > d away, all b are > d away.
    - After sorting arr2, bisect_left(arr2, a-d) gives us the smallest b
      >= a-d. If this b is > a+d, then no b in [a-d, a+d]. If this b is
      <= a+d, then there's a b in [a-d, a+d].

    Time:  O(n log m + m log m).
    Space: O(1) extra.
    """
    import bisect
    arr2.sort()
    count = 0
    for a in arr1:
        idx = bisect.bisect_left(arr2, a - d)
        if idx < len(arr2) and arr2[idx] <= a + d:
            continue  # There's a b in [a-d, a+d]
        count += 1
    return count


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to count elements in arr1 that are 'far' from all elements in arr2,
where 'far' means distance > d."

Key Insight:
"Sort arr2. For each a in arr1, find the smallest b in arr2 with b >= a-d.
If that b is <= a+d, then there's an arr2 element too close to a, so skip a.
Otherwise, count a."

Algorithm:
"1. Sort arr2.
2. For each a in arr1:
   a. idx = bisect_left(arr2, a - d). Find first b >= a-d.
   b. If idx < len(arr2) and arr2[idx] <= a+d: skip (close element exists).
   c. Else: count a.
3. Return count."

Why this works:
"After sorting arr2, the closest arr2 element to a is either:
- The largest b <= a (need to check it).
- The smallest b >= a (need to check it).
If both are > d away, then all b are > d away.

The first b >= a-d is a candidate. If it's also <= a+d, it's in the danger
zone. If it's > a+d, then no b is in [a-d, a+d] (because all later b are
even larger)."

Edge cases:
- Empty arr1: return 0.
- Empty arr2: all arr1 elements are far (return len(arr1)).
- d=0: only count a with no exact match in arr2.
- All same arr1 elements: same answer.

Complexity:
- Time:  O(n log m + m log m) where n = len(arr1), m = len(arr2).
- Space: O(1) extra (sorting in place).

KEY TRICK:
Sort arr2, use bisect_left to find first b >= a-d. Check if b <= a+d.

ALTERNATIVE: Brute force
For each a, check all b. O(n*m). Easy but slow.

ALTERNATIVE: Set lookup
Build set of arr2. For each a, check if any value in [a-d, a+d] is in set.
O(n*d) per a, O(n*d) total. Better when d is small.

ALTERNATIVE: numpy
Broadcast subtraction, find min distance per a, count those > d. Same
complexity, faster in practice for large inputs.

RELATIONSHIP TO OTHER PROBLEMS:
- Two Sum Closest (LC 16): Find closest sum, similar binary search.
- K-diff Pairs in Array (LC 532): Pair with abs difference <= k.
- Contains Duplicate III (LC 220): Within k distance AND t value diff.

INTERVIEW TIPS:
1. Mention sorting + binary search approach.
2. Note the brute force as a fallback.
3. Discuss why the closest element check is sufficient.
4. Handle empty arrays.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort + bisect (BEST)", find_the_distance_value_1),
        ("Way 2: Verbose", find_the_distance_value_2),
        ("Way 3: Brute force", find_the_distance_value_3),
        ("Way 4: all()", find_the_distance_value_4),
        ("Way 5: Set lookup", find_the_distance_value_5),
        ("Way 6: Counter", find_the_distance_value_6),
        ("Way 7: Manual binary search", find_the_distance_value_7),
        ("Way 8: bisect_right count", find_the_distance_value_8),
        ("Way 9: Sort + early exit", find_the_distance_value_9),
        ("Way 10: enumerate", find_the_distance_value_10),
        ("Way 11: Class-based", find_the_distance_value_11),
        ("Way 12: Inline sorted", find_the_distance_value_12),
        ("Way 13: numpy", find_the_distance_value_13),
        ("Way 14: Generator", find_the_distance_value_14),
        ("Way 15: Set with range", find_the_distance_value_15),
        ("Way 16: Two-pointer", find_the_distance_value_16),
        ("Way 17: any/all", find_the_distance_value_17),
        ("Way 18: List comprehension", find_the_distance_value_18),
        ("Way 19: Closest b check", find_the_distance_value_19),
        ("Way 20: Final cleanest", find_the_distance_value_20),
    ]

    test_cases = [
        # Educative examples
        # arr1=[4,5,8], arr2=[10,9,1,8], d=2
        # 4: |4-10|=6,|4-9|=5,|4-1|=3,|4-8|=4 -> all > 2 -> count
        # 5: |5-10|=5,|5-9|=4,|5-1|=4,|5-8|=3 -> all > 2 -> count
        # 8: |8-8|=0 <= 2 -> skip
        # Total = 2
        ([4, 5, 8], [10, 9, 1, 8], 2, 2),

        # arr1=[1,4,2,3], arr2=[-4,-3,6,10,20,15], d=3
        # 1: |1-(-4)|=5,|1-(-3)|=4,|1-6|=5,|1-10|=9,|1-20|=19,|1-15|=14 -> all > 3 -> count
        # 4: |4-(-4)|=8,|4-(-3)|=7,|4-6|=2 <= 3 -> skip
        # 2: |2-(-4)|=6,|2-(-3)|=5,|2-6|=4,|2-10|=8,|2-20|=18,|2-15|=13 -> all > 3 -> count
        # 3: |3-(-4)|=7,|3-(-3)|=6,|3-6|=3 <= 3 -> skip
        # Total = 2
        ([1, 4, 2, 3], [-4, -3, 6, 10, 20, 15], 3, 2),

        # Single element
        ([5], [1, 10], 2, 1),  # |5-1|=4, |5-10|=5, both > 2 -> count

        # Empty arr1
        ([], [1, 2, 3], 1, 0),

        # Empty arr2
        ([1, 2, 3], [], 0, 3),

        # All close
        ([1, 2, 3], [1, 2, 3], 0, 0),  # All exact matches, all skip

        # All far
        ([1, 2, 3], [100, 200, 300], 10, 3),  # All far

        # d=0, no exact matches
        ([1, 2, 3], [4, 5, 6], 0, 3),

        # d=0, has exact match
        ([1, 2, 3], [2, 5, 6], 0, 2),  # 2 has exact match

        # Negative numbers
        ([-5, -3, 0], [-1, 1, 2], 2, 1),  # -3: |-3-(-1)|=2, skip. -5 and 0 far.
        # -5: |-5-(-1)|=4, |-5-1|=6, |-5-2|=7 -> all > 2 -> count
        # -3: |-3-(-1)|=2 <= 2 -> skip
        # 0: |0-(-1)|=1 <= 2 -> skip
        # Total = 1

        # Boundary: d very large
        ([1, 2, 3], [1, 2, 3], 100, 0),  # All within 100

        # Mixed
        ([4, 5, 8], [10, 9, 1, 8], 0, 2),  # Same as d=2 but exclude exact
        # 4: |4-8|=4 > 0 -> count
        # 5: |5-8|=3 > 0 -> count
        # 8: |8-8|=0 <= 0 -> skip
        # Total = 2

        # Larger example
        ([1, 5, 10, 15, 20], [3, 7, 12, 18], 2, 1),
        # 1: |1-3|=2 <= 2 -> skip
        # 5: |5-3|=2, |5-7|=2 -> both <= 2 -> skip
        # 10: |10-7|=3, |10-12|=2 <= 2 -> skip
        # 15: |15-12|=3, |15-18|=3 -> both > 2 -> count
        # 20: |20-18|=2 <= 2 -> skip
        # Total = 1
    ]

    print("=" * 70)
    print("FIND THE DISTANCE VALUE - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/find-the-distance-value-between-two-arrays")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for arr1, arr2, d, expected in test_cases:
            try:
                import copy
                result = func(copy.deepcopy(arr1), copy.deepcopy(arr2), d)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: arr1={arr1}, arr2={arr2}, d={d} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on arr1={arr1}, arr2={arr2}, d={d} - {e}")
        if all_test_pass:
            print(f"  OK {name}: PASS")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)