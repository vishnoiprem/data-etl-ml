"""
Squares of a Sorted Array - 20 Ways
====================================
Given an integer array nums sorted in non-decreasing order, return an
array of the squares of each number, also sorted in non-decreasing order.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/squares-of-a-sorted-array

Examples:
    [-4, -1, 0, 3, 10]     -> [0, 1, 9, 16, 100]
    [-7, -3, 2, 3, 11]     -> [4, 9, 9, 49, 121]
    [0, 1]                  -> [0, 1]
    [-5, -3, -2, -1]        -> [1, 4, 9, 25]
    [-1]                    -> [1]

Constraints:
- 1 <= n <= 10^4
- -10^4 <= nums[i] <= 10^4
- nums is sorted in non-decreasing order.

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Square each element of a sorted array; the negatives produce the
    largest values. Return the result sorted."

2. KEY INSIGHT:
   "After squaring, the largest values come from the OUTER ends of the
    array (negative left and positive right). Two-pointer from both ends:
    pick the larger |x|, place at result tail, advance inward."

3. PATTERN RECOGNITION:
   "Two-pointer filling an output array from the back (descending fill)."

4. EDGE CASES:
   - All non-negative -> trivially square each in order.
   - All negative -> result is square in reverse order.
   - Mixed signs -> pointer work.
   - Single element -> square and return.
   - Zero -> squared is zero, doesn't disturb ordering.

5. TRICKY DETAIL:
   "ALWAYS compare absolute values, not the signed values. The largest
    |x| can be on either end depending on how the negatives extend vs
    positives. Don't just grab nums[left]^2."

6. ALGORITHM:
   "i, j = 0, n-1; result = [0]*n
    for k in range(n-1, -1, -1):
        if abs(nums[i]) > abs(nums[j]):
            result[k] = nums[i] ** 2; i += 1
        else:
            result[k] = nums[j] ** 2; j -= 1
    return result"

7. WHY IT WORKS:
   "Square function is monotonic for |x| >= 0. The maximum |x| at each
    step must come from one end of the remaining array. Filling from
    the back yields the largest first."

8. COMPLEXITY:
   "Time: O(n).
    Space: O(n) for the output array (or O(1) if in-place allowed)."

9. CODE STRUCTURE:
   "Two pointers i, j. Loop from k=n-1 down to 0. Place winner at result[k]."

10. MENTAL TRACE:
    [-4, -1, 0, 3, 10]:
    k=4: |-4|=4 vs |10|=10 -> result[4]=100, j=3
    k=3: |-4|=4 vs |3|=3   -> result[3]=16, i=1
    k=2: |-1|=1 vs |3|=3   -> result[2]=9, j=2
    k=1: |-1|=1 vs |0|=0   -> result[1]=1, i=2
    k=0: |0|=0 vs |0|=0   -> result[0]=0, j=1
    Result: [0, 1, 9, 16, 100] ✓
"""


# Solution 1: Canonical two-pointer (BEST)
def sorted_squares_v1(nums):
    n = len(nums)
    result = [0] * n
    i, j = 0, n - 1
    for k in range(n - 1, -1, -1):
        if abs(nums[i]) > abs(nums[j]):
            result[k] = nums[i] ** 2
            i += 1
        else:
            result[k] = nums[j] ** 2
            j -= 1
    return result


# Solution 2: Canonical w/ while loop (BEST alternative)
def sorted_squares_v2(nums):
    n = len(nums)
    result = [0] * n
    i, j = 0, n - 1
    k = n - 1
    while i <= j:
        if abs(nums[i]) > abs(nums[j]):
            result[k] = nums[i] * nums[i]
            i += 1
        else:
            result[k] = nums[j] * nums[j]
            j -= 1
        k -= 1
    return result


# Solution 3: Find split point, then merge two ascending halves
def sorted_squares_v3(nums):
    # Find first non-negative index
    n = len(nums)
    if n == 0:
        return []
    split = 0
    while split < n and nums[split] < 0:
        split += 1
    # Now nums[split] >= 0; left side is negative (descending in abs value when reversed)
    left = nums[:split][::-1]   # ascending abs values from neg side
    right = nums[split:]        # ascending positives
    # Merge two ascending-by-abs lists
    result = []
    p1 = p2 = 0
    while p1 < len(left) and p2 < len(right):
        if left[p1] * left[p1] <= right[p2] * right[p2]:
            result.append(left[p1] * left[p1])
            p1 += 1
        else:
            result.append(right[p2] * right[p2])
            p2 += 1
    while p1 < len(left):
        result.append(left[p1] * left[p1])
        p1 += 1
    while p2 < len(right):
        result.append(right[p2] * right[p2])
        p2 += 1
    return result


# Solution 4: Brute force — square + sort
def sorted_squares_v4(nums):
    return sorted(x * x for x in nums)


# Solution 5: list comprehension + sorted
def sorted_squares_v5(nums):
    return sorted([x ** 2 for x in nums])


# Solution 6: Using map + sorted
def sorted_squares_v6(nums):
    return sorted(map(lambda x: x * x, nums))


# Solution 7: Two-pointer with negative-aware swap first, then sort
def sorted_squares_v7(nums):
    # Find split between negative and non-negative
    n = len(nums)
    left = 0
    right = n - 1
    # Build from back using direct comparison
    result = [0] * n
    k = n - 1
    while left <= right:
        if abs(nums[left]) >= abs(nums[right]):
            result[k] = nums[left] ** 2
            left += 1
        else:
            result[k] = nums[right] ** 2
            right -= 1
        k -= 1
    return result


# Solution 8: Recursive two-pointer
def sorted_squares_v8(nums):
    n = len(nums)
    result = [0] * n

    def helper(i, j, k):
        if i > j:
            return
        if abs(nums[i]) > abs(nums[j]):
            result[k] = nums[i] ** 2
            helper(i + 1, j, k - 1)
        else:
            result[k] = nums[j] ** 2
            helper(i, j - 1, k - 1)
    helper(0, n - 1, n - 1)
    return result


# Solution 9: Use numpy
def sorted_squares_v9(nums):
    try:
        import numpy as np
        return list(np.sort(np.array(nums) ** 2))
    except ImportError:
        return sorted(x * x for x in nums)


# Solution 10: Sort by abs then square
def sorted_squares_v10(nums):
    return [(abs(x)) ** 2 for x in sorted(nums, key=abs, reverse=True)][::-1]


# Solution 11: Split + ascending merge
def sorted_squares_v11(nums):
    n = len(nums)
    # Find split
    split = 0
    while split < n and nums[split] < 0:
        split += 1
    # Neg side (descending in input, but ascending in abs when reversed)
    neg = nums[:split][::-1]   # ascending abs values from neg side
    pos = nums[split:]
    # Merge two ascending-by-abs lists into ascending squared
    result = []
    i = j = 0
    while i < len(neg) and j < len(pos):
        if neg[i] * neg[i] <= pos[j] * pos[j]:
            result.append(neg[i] * neg[i])
            i += 1
        else:
            result.append(pos[j] * pos[j])
            j += 1
    while i < len(neg):
        result.append(neg[i] * neg[i])
        i += 1
    while j < len(pos):
        result.append(pos[j] * pos[j])
        j += 1
    return result


# Solution 12: Two-pointer using heap (educational)
def sorted_squares_v12(nums):
    import heapq
    # Use a max-heap by abs value, but heapq is min-heap so negate.
    # Simpler: just collect all squared values and sort.
    # This is essentially the brute-force variant.
    work = [(abs(x), x * x) for x in nums]
    work.sort(key=lambda t: t[0])
    return [sq for _, sq in work]


# Solution 13: Brute + filter + sort (educational)
def sorted_squares_v13(nums):
    squared = []
    for x in nums:
        squared.append(x ** 2)
    squared.sort()
    return squared


# Solution 14: list comp inside sorted with explicit map
def sorted_squares_v14(nums):
    squares = list(map(lambda x: x ** 2, nums))
    squares.sort()
    return squares


# Solution 15: Two-pointer with manual index
def sorted_squares_v15(nums):
    n = len(nums)
    output = [None] * n
    left, right = 0, n - 1
    pos = n - 1
    while left <= right:
        lsq = nums[left] * nums[left]
        rsq = nums[right] * nums[right]
        if lsq > rsq:
            output[pos] = lsq
            left += 1
        else:
            output[pos] = rsq
            right -= 1
        pos -= 1
    return output


# Solution 16: Using list comprehension with enumerate
def sorted_squares_v16(nums):
    return sorted([v ** 2 for v in nums])


# Solution 17: Stable approach using abs key
def sorted_squares_v17(nums):
    return [v ** 2 for v in sorted(nums, key=lambda x: abs(x))]


# Solution 18: Stable ascending using abs reverse trick
def sorted_squares_v18(nums):
    # abs is non-negative; sort ascending; square each
    return [v ** 2 for v in sorted(nums, key=abs)]


# Solution 19: Two-pointer producing ascending output (reverse result)
def sorted_squares_v19(nums):
    n = len(nums)
    result = [0] * n
    i, j = 0, n - 1
    for k in range(n - 1, -1, -1):
        if abs(nums[i]) >= abs(nums[j]):
            result[k] = nums[i] ** 2
            i += 1
        else:
            result[k] = nums[j] ** 2
            j -= 1
    return result


# Solution 20: Concurrent split + merge with reversed negative side
def sorted_squares_v20(nums):
    n = len(nums)
    if n == 0:
        return []
    # Locate pivot (first non-negative)
    p = 0
    while p < n and nums[p] < 0:
        p += 1
    # Sorted negative portion in ascending order (by absolute value): nums[:p][::-1]
    # Sorted positive portion in ascending order: nums[p:]
    neg_asc = list(reversed(nums[:p]))  # ascending abs
    pos_asc = nums[p:]                  # already ascending
    # Merge
    i = j = 0
    out = []
    while i < len(neg_asc) and j < len(pos_asc):
        if neg_asc[i] ** 2 <= pos_asc[j] ** 2:
            out.append(neg_asc[i] ** 2)
            i += 1
        else:
            out.append(pos_asc[j] ** 2)
            j += 1
    while i < len(neg_asc):
        out.append(neg_asc[i] ** 2)
        i += 1
    while j < len(pos_asc):
        out.append(pos_asc[j] ** 2)
        j += 1
    return out


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (canonical 2ptr)",       sorted_squares_v1),
        ("V2 (while loop)",           sorted_squares_v2),
        ("V3 (split + merge)",        sorted_squares_v3),
        ("V4 (brute square+sort)",    sorted_squares_v4),
        ("V5 (list comp + sorted)",   sorted_squares_v5),
        ("V6 (map + sorted)",         sorted_squares_v6),
        ("V7 (>= variant)",           sorted_squares_v7),
        ("V8 (recursive)",            sorted_squares_v8),
        ("V9 (numpy)",                sorted_squares_v9),
        ("V10 (sort by abs)",         sorted_squares_v10),
        ("V11 (deque merge)",         sorted_squares_v11),
        ("V12 (heap sort)",           sorted_squares_v12),
        ("V13 (brute sort)",          sorted_squares_v13),
        ("V14 (map)",                 sorted_squares_v14),
        ("V15 (manual idx)",          sorted_squares_v15),
        ("V16 (list comp)",           sorted_squares_v16),
        ("V17 (key=abs asc)",         sorted_squares_v17),
        ("V18 (key=abs sorted)",      sorted_squares_v18),
        ("V19 (>= variant)",          sorted_squares_v19),
        ("V20 (split+merge v2)",      sorted_squares_v20),
    ]

    test_cases = [
        ([-4, -1, 0, 3, 10],     [0, 1, 9, 16, 100]),
        ([-7, -3, 2, 3, 11],     [4, 9, 9, 49, 121]),
        ([0, 1],                  [0, 1]),
        ([-5, -3, -2, -1],        [1, 4, 9, 25]),
        ([-1],                    [1]),
        ([-3, -2, -1],            [1, 4, 9]),
        ([1, 2, 3, 4],            [1, 4, 9, 16]),
        ([-1, 0, 0, 1],           [0, 0, 1, 1]),
        ([-10000],                [100000000]),
        ([-5, -4, -3, -2, 0],     [0, 4, 9, 16, 25]),
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