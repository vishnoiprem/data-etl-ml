"""
Next Permutation - 10 Ways
==========================
Given an integer array nums, rearrange it into the lexicographically next
greater permutation in-place. If no such permutation exists (i.e., the array
is in descending order), reset to the smallest (ascending) order.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/next-permutation

Examples:
    [4,5,6]        -> [4,6,5]
    [5,6,4]        -> [6,4,5]
    [6,5,4]        -> [4,5,6]  (wraparound)
    [1,2,3]        -> [1,3,2]
    [1,1,5]        -> [1,5,1]
    [1]            -> [1]

Constraints:
- 1 <= n <= 100
- 0 <= nums[i] <= 100

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Find the next lexicographic permutation, in-place. Wrap around if needed."

2. KEY INSIGHT:
   "Find the first i from the right where nums[i] < nums[i+1] (the 'pivot').
    Then find the first j > i from the right where nums[j] > nums[i] (just
    larger than pivot). Swap them. Then reverse the suffix i+1..n-1."

3. PATTERN RECOGNITION:
   "Two-pointer / scan from the right for pivot + successor, then reverse."

4. EDGE CASES:
   - Already descending (e.g., [3,2,1]) -> reverse entire array.
   - Already ascending (e.g., [1,2,3]) -> swap last two.
   - Single element -> no change.
   - All same elements (e.g., [2,2,2]) -> no change.

5. TRICKY DETAIL:
   "Reversing the suffix after the swap is what gives the LEXICOGRAPHICALLY
    SMALLEST next permutation. If you just sorted the suffix, it would
    still be valid but not the next smallest (would skip over valid
    permutations)."

6. ALGORITHM:
   "1. Find pivot i = largest index with nums[i] < nums[i+1].
       If none, reverse the entire array.
    2. Find swap j = largest index > i with nums[j] > nums[i].
    3. Swap nums[i] and nums[j].
    4. Reverse nums[i+1..n-1]."

7. WHY IT WORKS:
   "The pivot is where the right tail stops being strictly decreasing.
    Swapping with the smallest 'just-larger' element and then reversing
    (which places the suffix in ascending order) yields the smallest
    possible next permutation."

8. COMPLEXITY:
   "Time: O(n).
    Space: O(1)."

9. CODE STRUCTURE:
   "find pivot from right (first nums[i] < nums[i+1])
    if no pivot: reverse and done
    find swap from right (first nums[j] > nums[i])
    swap nums[i], nums[j]
    reverse nums[i+1:]"

10. MENTAL TRACE:
    [5,6,4,3,2]:
    - From right, find pivot: nums[0]=5 < nums[1]=6, so i=0.
    - From right, find j where nums[j] > 5: nums[1]=6 > 5 → j=1.
    - Swap: [6,5,4,3,2]
    - Reverse suffix [5,4,3,2]? Wait, i=0 so we reverse nums[1:] = [5,4,3,2] → [2,3,4,5].
    - Result: [6,2,3,4,5] ✓
"""


# Solution 1: Canonical (BEST)
def next_perm_v1(nums):
    n = len(nums)
    if n <= 1:
        return nums
    # Step 1: find pivot
    i = n - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1
    if i >= 0:
        # Step 2: find j
        j = n - 1
        while nums[j] <= nums[i]:
            j -= 1
        # Step 3: swap
        nums[i], nums[j] = nums[j], nums[i]
    # Step 4: reverse suffix
    nums[i + 1:] = nums[i + 1:][::-1]
    return nums


# Solution 2: Using in-place reverse with two-pointer
def next_perm_v2(nums):
    n = len(nums)
    if n <= 1:
        return nums
    # Find pivot
    i = n - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1
    if i >= 0:
        # Find successor
        j = n - 1
        while nums[j] <= nums[i]:
            j -= 1
        nums[i], nums[j] = nums[j], nums[i]
    # Reverse suffix in place using two-pointer
    lo, hi = i + 1, n - 1
    while lo < hi:
        nums[lo], nums[hi] = nums[hi], nums[lo]
        lo += 1
        hi -= 1
    return nums


# Solution 3: Functional with reversed + bisect
def next_perm_v3(nums):
    import bisect
    n = len(nums)
    if n <= 1:
        return nums
    # Find pivot
    i = n - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1
    if i >= 0:
        # The suffix nums[i+1:] is in DESCENDING order (by pivot definition).
        # Reversed suffix is ASCENDING, so we can bisect on it.
        suffix_rev = nums[i + 1:][::-1]
        target = nums[i]
        # Find leftmost position in ascending suffix where value > target.
        # In reversed (ascending) suffix, that gives us the smallest
        # element > pivot; but we want the LARGEST such element in original
        # (rightmost in original). Since original suffix is descending, the
        # leftmost in reversed = rightmost in original. Good.
        idx = bisect.bisect_right(suffix_rev, target)
        if idx < len(suffix_rev):
            # Map back: position idx in suffix_rev corresponds to original idx
            # counted from the right. Original index = i + 1 + (len(suffix) - 1 - idx).
            j = i + 1 + (len(suffix_rev) - 1 - idx)
            nums[i], nums[j] = nums[j], nums[i]
    nums[i + 1:] = nums[i + 1:][::-1]
    return nums


# Solution 4: Using sorted suffix + swap + re-sort
def next_perm_v4(nums):
    """A simpler-but-suboptimal variant: sort suffix after swap."""
    n = len(nums)
    if n <= 1:
        return nums
    # Find pivot
    i = n - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1
    if i >= 0:
        # Find first j > i with nums[j] > nums[i] (from right)
        j = n - 1
        while nums[j] <= nums[i]:
            j -= 1
        nums[i], nums[j] = nums[j], nums[i]
        # Sort suffix (not the most efficient, but works)
        nums[i + 1:] = sorted(nums[i + 1:])
    else:
        nums.sort()
    return nums


# Solution 5: Recursive
def next_perm_v5(nums):
    n = len(nums)
    if n <= 1:
        return nums

    def find_pivot(arr, i):
        if i == 0:
            return -1
        if arr[i - 1] < arr[i]:
            return i - 1
        return find_pivot(arr, i - 1)

    def find_swap(arr, i, j):
        if arr[j] > arr[i]:
            return j
        return find_swap(arr, i, j - 1)

    def reverse(arr, lo, hi):
        if lo >= hi:
            return
        arr[lo], arr[hi] = arr[hi], arr[lo]
        reverse(arr, lo + 1, hi - 1)

    pivot = find_pivot(nums, n - 1)
    if pivot >= 0:
        swap = find_swap(nums, pivot, n - 1)
        nums[pivot], nums[swap] = nums[swap], nums[pivot]
        reverse(nums, pivot + 1, n - 1)
    else:
        reverse(nums, 0, n - 1)
    return nums


# Solution 6: Brute force — generate all, sort, find next
def next_perm_v6(nums):
    from itertools import permutations
    n = len(nums)
    if n <= 1:
        return nums
    all_perms = sorted(set(permutations(nums)))
    current = tuple(nums)
    idx = all_perms.index(current)
    if idx + 1 < len(all_perms):
        result = list(all_perms[idx + 1])
    else:
        result = list(all_perms[0])
    nums[:] = result
    return nums


# Solution 7: Two-pointer swap + custom reverse
def next_perm_v7(nums):
    n = len(nums)
    if n <= 1:
        return nums
    # Find pivot
    i = n - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1
    if i < 0:
        nums.reverse()
        return nums
    # Find j
    j = n - 1
    while nums[j] <= nums[i]:
        j -= 1
    nums[i], nums[j] = nums[j], nums[i]
    # Reverse nums[i+1:]
    left, right = i + 1, n - 1
    while left < right:
        nums[left], nums[right] = nums[right], nums[left]
        left += 1
        right -= 1
    return nums


# Solution 8: Using numpy (but mutating original)
def next_perm_v8(nums):
    try:
        import numpy as np
        n = len(nums)
        if n <= 1:
            return nums
        arr = np.array(nums)
        # Find pivot: scan from right
        i = n - 2
        while i >= 0 and arr[i] >= arr[i + 1]:
            i -= 1
        if i >= 0:
            # Find j
            j = n - 1
            while arr[j] <= arr[i]:
                j -= 1
            arr[i], arr[j] = arr[j], arr[i]
        # Reverse suffix
        suffix = arr[i + 1:][::-1]
        nums[:] = list(arr[:i + 1]) + list(suffix)
        return nums
    except ImportError:
        return next_perm_v1(nums)


# Solution 9: Using built-in reversed
def next_perm_v9(nums):
    n = len(nums)
    if n <= 1:
        return nums
    i = n - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1
    if i >= 0:
        j = n - 1
        while nums[j] <= nums[i]:
            j -= 1
        nums[i], nums[j] = nums[j], nums[i]
    suffix = list(reversed(nums[i + 1:]))
    nums[i + 1:] = suffix
    return nums


# Solution 10: With explicit step-by-step reversal
def next_perm_v10(nums):
    n = len(nums)
    if n <= 1:
        return nums
    # Find pivot
    pivot = -1
    for i in range(n - 2, -1, -1):
        if nums[i] < nums[i + 1]:
            pivot = i
            break
    if pivot == -1:
        nums.reverse()
        return nums
    # Find swap partner
    swap = -1
    for j in range(n - 1, pivot, -1):
        if nums[j] > nums[pivot]:
            swap = j
            break
    nums[pivot], nums[swap] = nums[swap], nums[pivot]
    # Reverse suffix
    nums[pivot + 1:] = nums[pivot + 1:][::-1]
    return nums


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (canonical)",            next_perm_v1),
        ("V2 (in-place reverse)",     next_perm_v2),
        ("V3 (bisect)",               next_perm_v3),
        ("V4 (sort suffix)",          next_perm_v4),
        ("V5 (recursive)",            next_perm_v5),
        ("V6 (brute force all perms)", next_perm_v6),
        ("V7 (two-pointer reverse)",  next_perm_v7),
        ("V8 (numpy)",                next_perm_v8),
        ("V9 (builtin reversed)",     next_perm_v9),
        ("V10 (step-by-step)",        next_perm_v10),
    ]

    test_cases = [
        # (input, expected)
        ([4, 5, 6],         [4, 6, 5]),
        ([5, 6, 4],         [6, 4, 5]),
        ([6, 5, 4],         [4, 5, 6]),
        ([1, 2, 3],         [1, 3, 2]),
        ([1, 1, 5],         [1, 5, 1]),
        ([1],               [1]),
        ([3, 2, 1],         [1, 2, 3]),
        ([1, 3, 2],         [2, 1, 3]),
        ([2, 3, 1],         [3, 1, 2]),
        ([1, 5, 1],         [5, 1, 1]),
        ([5, 1, 4, 3, 2],   [5, 2, 1, 3, 4]),
        ([2, 2, 2, 2],      [2, 2, 2, 2]),  # all same, no change
        ([1, 4, 3, 2],      [2, 1, 3, 4]),
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
                print(f"  X {name} [{idx}]: ERROR on {arr}: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
    print("\n=== INTERVIEW THINKING ===")
    print("""
1. UNDERSTAND:  Find the next lexicographic permutation in-place.
2. INSIGHT:     Find pivot (first nums[i] < nums[i+1] from right), then swap with rightmost nums[j] > pivot, reverse suffix.
3. PATTERN:     Right-to-left scan + reverse suffix.
4. EDGE:        Descending -> ascending (wrap); single element -> no-op; all-same -> no-op.
5. TRICKY:      Reverse (not sort) the suffix to get the SMALLEST next permutation.
6. ALGORITHM:   Find pivot; if none, reverse all; else find successor, swap, reverse suffix.
7. PROOF:       Pivot+just-larger-swap+reverse-suffix gives lex-smallest next perm.
8. COMPLEXITY:  O(n) time, O(1) space.
9. CODE:        Right-scan for pivot; right-scan for swap; reverse suffix.
10. TRACE:      [5,6,4,3,2]: pivot=0(nums[0]<nums[1]=6); j=1; swap [6,5,4,3,2]; reverse suffix to [6,2,3,4,5].
""")
