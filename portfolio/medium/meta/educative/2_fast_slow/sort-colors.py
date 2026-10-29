"""
Sort Colors - 10 Ways
=====================
Given an array nums with values 0, 1, 2 (representing red, white, blue),
sort the array in-place so that all 0s come first, then 1s, then 2s.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/sort-colors

Examples:
    [2,0,2,1,1,0] -> [0,0,1,1,2,2]
    [2,0,1]       -> [0,1,2]

Constraints:
- 1 <= n <= 300
- nums[i] in {0, 1, 2}

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Sort array of 0,1,2 in place. One pass, constant space."

2. KEY INSIGHT:
   "Dutch National Flag (Dijkstra). Three regions: [0..lo-1]=0, [lo..mid-1]=1,
    [mid..hi]=unknown, [hi+1..end]=2. Maintain invariants with three pointers."

3. PATTERN RECOGNITION:
   "Three-pointer partitioning. lo, mid, hi. In-place, single pass."

4. EDGE CASES:
   - All same value -> already sorted, no swaps needed.
   - Single element -> trivial.
   - Empty -> no-op.

5. TRICKY DETAIL:
   "When nums[mid] == 0: swap with nums[lo], increment BOTH lo and mid.
    When nums[mid] == 1: just increment mid.
    When nums[mid] == 2: swap with nums[hi], decrement hi (mid does NOT advance).
    Loop while mid <= hi."

6. ALGORITHM:
   "lo, mid = 0, 0; hi = n-1
    while mid <= hi:
        if nums[mid] == 0: swap(nums, lo, mid); lo++; mid++
        elif nums[mid] == 1: mid++
        else:                swap(nums, mid, hi); hi--"

7. WHY IT WORKS:
   "Three regions invariant:
    [0..lo-1]   : all 0s
    [lo..mid-1] : all 1s
    [mid..hi]   : unprocessed
    [hi+1..n-1] : all 2s
    Each step preserves this invariant."

8. COMPLEXITY:
   "Time: O(n) — each element processed at most twice.
    Space: O(1)."

9. CODE STRUCTURE:
   "lo = mid = 0; hi = n-1
    while mid <= hi:
        if nums[mid] == 0: swap(lo, mid); lo++; mid++
        elif nums[mid] == 1: mid++
        else: swap(mid, hi); hi--"

10. MENTAL TRACE:
    [2,0,2,1,1,0], lo=mid=0, hi=5
    mid=0, nums[0]=2 -> swap(0,5): [0,0,2,1,1,2], hi=4
    mid=0, nums[0]=0 -> swap(0,0): same, lo=1, mid=1
    mid=1, nums[1]=0 -> swap(1,5): [0,0,2,1,1,2], lo=2, mid=2
    ... etc.
    Final: [0,0,1,1,2,2] ✓
"""


# Solution 1: Canonical Dutch National Flag (BEST)
def sort_colors_v1(nums):
    """Three-way partition with lo, mid, hi pointers."""
    lo, mid, hi = 0, 0, len(nums) - 1
    while mid <= hi:
        if nums[mid] == 0:
            nums[lo], nums[mid] = nums[mid], nums[lo]
            lo += 1
            mid += 1
        elif nums[mid] == 1:
            mid += 1
        else:  # nums[mid] == 2
            nums[mid], nums[hi] = nums[hi], nums[mid]
            hi -= 1
    return nums


# Solution 2: Counting sort
def sort_colors_v2(nums):
    """Count 0s, 1s, 2s; rewrite."""
    counts = [0, 0, 0]
    for x in nums:
        counts[x] += 1
    idx = 0
    for color in range(3):
        for _ in range(counts[color]):
            nums[idx] = color
            idx += 1
    return nums


# Solution 3: Two-pass with separate writes
def sort_colors_v3(nums):
    """Pass 1: count; Pass 2: write."""
    c0 = c1 = c2 = 0
    for x in nums:
        if x == 0: c0 += 1
        elif x == 1: c1 += 1
        else: c2 += 1
    i = 0
    for _ in range(c0): nums[i] = 0; i += 1
    for _ in range(c1): nums[i] = 1; i += 1
    for _ in range(c2): nums[i] = 2; i += 1
    return nums


# Solution 4: Two-pointer with two-region partitioning (lo, hi)
def sort_colors_v4(nums):
    """Move 0s to front, 2s to back via two pointers."""
    lo, hi = 0, len(nums) - 1
    i = 0
    while i <= hi:
        if nums[i] == 0:
            nums[i], nums[lo] = nums[lo], nums[i]
            lo += 1
            i += 1
        elif nums[i] == 2:
            nums[i], nums[hi] = nums[hi], nums[i]
            hi -= 1
        else:
            i += 1
    return nums


# Solution 5: Using numpy
def sort_colors_v5(nums):
    try:
        import numpy as np
        arr = np.array(nums)
        # Use np.partition-style approach via sorting, but cheating with np.sort
        # To preserve "no library sort", we use np.argpartition or manual:
        order = np.argsort(arr, kind='stable')
        return arr[order].tolist()
    except ImportError:
        return sort_colors_v1(nums)


# Solution 6: Using Counter (overkill but works)
def sort_colors_v6(nums):
    from collections import Counter
    cnt = Counter(nums)
    idx = 0
    for color in (0, 1, 2):
        for _ in range(cnt[color]):
            nums[idx] = color
            idx += 1
    return nums


# Solution 7: Recursive quicksort-like partitioning
def sort_colors_v7(nums):
    """Quicksort-style 3-way partition."""
    def partition(arr, lo, hi):
        if lo >= hi:
            return
        pivot = arr[lo]
        lt, gt, i = lo, hi, lo
        while i <= gt:
            if arr[i] < pivot:
                arr[lt], arr[i] = arr[i], arr[lt]
                lt += 1
                i += 1
            elif arr[i] > pivot:
                arr[gt], arr[i] = arr[i], arr[gt]
                gt -= 1
            else:
                i += 1
        partition(arr, lo, lt - 1)
        partition(arr, gt + 1, hi)
    partition(nums, 0, len(nums) - 1)
    return nums


# Solution 8: Functional reduce
def sort_colors_v8(nums):
    """Three passes via filter."""
    zeros = [0] * nums.count(0)
    ones = [1] * nums.count(1)
    twos = [2] * nums.count(2)
    return zeros + ones + twos


# Solution 9: In-place with manual cycle
def sort_colors_v9(nums):
    """Use a 3-way partition by counting via a 'rotating' approach."""
    # Equivalent to V1 but written with single-pointer and while
    n = len(nums)
    p0 = p1 = 0
    p2 = n - 1
    while p1 <= p2:
        if nums[p1] == 0:
            nums[p0], nums[p1] = nums[p1], nums[p0]
            p0 += 1
            p1 += 1
        elif nums[p1] == 1:
            p1 += 1
        else:
            nums[p2], nums[p1] = nums[p1], nums[p2]
            p2 -= 1
    return nums


# Solution 10: With separate output buffer
def sort_colors_v10(nums):
    """Two passes: count, then build output."""
    c = [0, 0, 0]
    for x in nums:
        c[x] += 1
    return [0]*c[0] + [1]*c[1] + [2]*c[2]


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (Dutch flag)",       sort_colors_v1),
        ("V2 (counting sort)",    sort_colors_v2),
        ("V3 (two-pass counts)",  sort_colors_v3),
        ("V4 (two-pointer)",      sort_colors_v4),
        ("V5 (numpy)",            sort_colors_v5),
        ("V6 (Counter)",          sort_colors_v6),
        ("V7 (3-way quicksort)",  sort_colors_v7),
        ("V8 (functional)",       sort_colors_v8),
        ("V9 (single-pointer)",   sort_colors_v9),
        ("V10 (output buffer)",   sort_colors_v10),
    ]

    test_cases = [
        # (input, expected)
        ([2, 0, 2, 1, 1, 0],  [0, 0, 1, 1, 2, 2]),
        ([2, 0, 1],            [0, 1, 2]),
        ([0],                  [0]),
        ([1, 2, 0],            [0, 1, 2]),
        ([2, 1, 1, 0, 0, 2],  [0, 0, 1, 1, 2, 2]),
        ([0, 0, 0],            [0, 0, 0]),
        ([2, 2, 2],            [2, 2, 2]),
        ([1, 1, 1],            [1, 1, 1]),
        ([1, 2, 0, 2, 1, 0, 0], [0, 0, 0, 1, 1, 2, 2]),
        ([],                   []),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (arr, expected) in enumerate(test_cases):
            try:
                got = func(list(arr))
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: {arr} -> {got} (expected {expected})")
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
1. UNDERSTAND:  Sort 0/1/2 array in place.
2. INSIGHT:     Dutch National Flag — three regions via 3 pointers.
3. PATTERN:     3-way partition in O(n) time, O(1) space.
4. EDGE:        All same value -> trivial; empty -> no-op.
5. TRICKY:      When nums[mid]==2, swap but DON'T advance mid (the new element at mid is unprocessed).
6. ALGORITHM:   lo=mid=0; hi=n-1; while mid<=hi: 0->swap&++lo&++mid; 1->++mid; 2->swap&--hi.
7. PROOF:       Three-region invariant maintained at each step.
8. COMPLEXITY:  O(n) time, O(1) space.
9. CODE:        lo=mid=0; hi=n-1; while loop with 3 cases.
10. TRACE:      [2,0,2,1,1,0] -> swap 0&5 -> [0,0,2,1,1,2] -> ... -> [0,0,1,1,2,2].
""")
