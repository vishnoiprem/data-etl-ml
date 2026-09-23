"""
Minimum Size Subarray Sum - 10 Ways
===================================
Given an array of positive integers nums and a positive integer target,
return the minimal length of a contiguous subarray of which the sum is
at least target. If no such subarray exists, return 0.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-size-subarray-sum
          (LeetCode #209)

Examples:
    target = 7, nums = [2,3,1,2,4,3]      -> 2  ([4,3])
    target = 4, nums = [1,4,4]            -> 1  ([4])
    target = 11, nums = [1,1,1,1,1,1,1,1] -> 0
    target = 11, nums = [1,2,3,4,5]       -> 3  ([3,4,5])

Constraints:
- 1 <= target <= 10^9
- 1 <= nums.length <= 10^5
- 1 <= nums[i] <= 10^4 (positive integers — important!)

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Find the smallest contiguous subarray with sum >= target. All nums
    are positive."

2. KEY INSIGHT:
   "Sliding window: expand right; while sum >= target, shrink left
    and update best."

3. PATTERN RECOGNITION:
   "Two pointers. Both move only forward. Each element added and
    removed at most once."

4. EDGE CASES:
   - All nums less than target -> 0.
   - Single element >= target -> 1.
   - Sum of all nums < target -> 0.

5. TRICKY DETAIL:
   "nums are POSITIVE. This means shrinking the window only decreases
    the sum, so the inner while-loop terminates. If negatives were
    allowed, this approach wouldn't work."

6. ALGORITHM:
   "left = 0; cur_sum = 0; best = inf
    for right in range(n):
        cur_sum += nums[right]
        while cur_sum >= target:
            best = min(best, right - left + 1)
            cur_sum -= nums[left]
            left += 1
    return 0 if best == inf else best"

7. WHY IT WORKS:
   "Each pair (left, right) is visited at most once. When sum >= target,
    we record the window and try to shrink it. The smallest such window
    for each right gives the answer."

8. COMPLEXITY:
   "Time: O(n) - each element added once and removed once.
    Space: O(1)."

9. CODE STRUCTURE:
   "Two pointers with cur_sum. Expand right, shrink left while valid."

10. MENTAL TRACE:
    target = 7, nums = [2,3,1,2,4,3]:
    left=0, cur=0, best=inf.
    right=0 (2): cur=2. <7.
    right=1 (3): cur=5. <7.
    right=2 (1): cur=6. <7.
    right=3 (2): cur=8. >=7! best=4 (window [0..3]). shrink: cur=8-2=6. left=1.
    right=4 (4): cur=10. >=7! best=min(4,4)=4 (window [1..4]). shrink: cur=10-3=7, left=2. >=7: best=min(4,3)=3. shrink: cur=7-1=6, left=3.
    right=5 (3): cur=9. >=7! best=min(3,3)=3 (window [3..5]). shrink: cur=9-2=7, left=4. >=7: best=min(3,2)=2. shrink: cur=7-4=3, left=5.
    Return 2. ✓
"""


# Solution 1: Sliding window (BEST)
def min_subarray_len_v1(target, nums):
    n = len(nums)
    left = 0
    cur_sum = 0
    best = float('inf')
    for right in range(n):
        cur_sum += nums[right]
        while cur_sum >= target:
            if right - left + 1 < best:
                best = right - left + 1
            cur_sum -= nums[left]
            left += 1
    return 0 if best == float('inf') else best


# Solution 2: Sliding window with prefix sum tracking
def min_subarray_len_v2(target, nums):
    # Same as V1 but using different variable names
    n = len(nums)
    if n == 0:
        return 0
    left = 0
    s = 0
    best = n + 1  # max possible + 1
    for right in range(n):
        s += nums[right]
        while s >= target:
            if right - left + 1 < best:
                best = right - left + 1
            s -= nums[left]
            left += 1
    return best if best <= n else 0


# Solution 3: Brute force O(n^2)
def min_subarray_len_v3(target, nums):
    n = len(nums)
    best = float('inf')
    for i in range(n):
        s = 0
        for j in range(i, n):
            s += nums[j]
            if s >= target:
                if j - i + 1 < best:
                    best = j - i + 1
                break
    return 0 if best == float('inf') else best


# Solution 4: Prefix sum + binary search
def min_subarray_len_v4(target, nums):
    import bisect
    n = len(nums)
    if n == 0:
        return 0
    # Build prefix sum: prefix[i] = sum(nums[0..i-1])
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]
    best = float('inf')
    # For each i, find smallest j such that prefix[j] - prefix[i] >= target
    # That means prefix[j] >= prefix[i] + target
    for i in range(n + 1):
        need = prefix[i] + target
        j = bisect.bisect_left(prefix, need, i + 1)
        if j <= n:
            if j - i < best:
                best = j - i
    return 0 if best == float('inf') else best


# Solution 5: itertools.accumulate + binary search
def min_subarray_len_v5(target, nums):
    import bisect
    from itertools import accumulate
    n = len(nums)
    if n == 0:
        return 0
    prefix = [0] + list(accumulate(nums))
    best = float('inf')
    for i in range(n + 1):
        need = prefix[i] + target
        j = bisect.bisect_left(prefix, need, i + 1)
        if j <= n:
            if j - i < best:
                best = j - i
    return 0 if best == float('inf') else best


# Solution 6: numpy prefix sum
def min_subarray_len_v6(target, nums):
    try:
        import numpy as np
        n = len(nums)
        if n == 0:
            return 0
        arr = np.array(nums)
        prefix = np.zeros(n + 1)
        prefix[1:] = np.cumsum(arr)
        # For each i, find smallest j with prefix[j] >= prefix[i] + target
        best = float('inf')
        for i in range(n + 1):
            need = prefix[i] + target
            j = np.searchsorted(prefix, need, side='left')
            if j < i + 1:
                j = i + 1
            if j <= n:
                if j - i < best:
                    best = int(j - i)
        return 0 if best == float('inf') else best
    except ImportError:
        return min_subarray_len_v1(target, nums)


# Solution 7: Sliding window with deque (overkill)
def min_subarray_len_v7(target, nums):
    from collections import deque
    # Same as V1 but store the window in a deque for educational purposes
    n = len(nums)
    if n == 0:
        return 0
    window = deque()
    cur = 0
    best = float('inf')
    for right in range(n):
        window.append(nums[right])
        cur += nums[right]
        while cur >= target and window:
            if len(window) < best:
                best = len(window)
            cur -= window.popleft()
    return 0 if best == float('inf') else best


# Solution 8: Recursive
def min_subarray_len_v8(target, nums):
    n = len(nums)
    best = [float('inf')]
    left = [0]
    cur = [0]

    def helper(right):
        if right == n:
            return
        cur[0] += nums[right]
        while cur[0] >= target and left[0] <= right:
            if right - left[0] + 1 < best[0]:
                best[0] = right - left[0] + 1
            cur[0] -= nums[left[0]]
            left[0] += 1
        helper(right + 1)

    helper(0)
    return 0 if best[0] == float('inf') else best[0]


# Solution 9: Sliding window with prefix sum inside
def min_subarray_len_v9(target, nums):
    # Use prefix sums in a sliding window
    n = len(nums)
    if n == 0:
        return 0
    best = float('inf')
    left = 0
    cur = 0
    for right in range(n):
        cur += nums[right]
        while cur >= target and left <= right:
            if right - left + 1 < best:
                best = right - left + 1
            cur -= nums[left]
            left += 1
    return 0 if best == float('inf') else best


# Solution 10: Final cleanest
def min_subarray_len_v10(target, nums):
    left = 0
    cur = 0
    best = float('inf')
    for right, x in enumerate(nums):
        cur += x
        while cur >= target:
            best = min(best, right - left + 1)
            cur -= nums[left]
            left += 1
    return 0 if best == float('inf') else best


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (BEST)",              min_subarray_len_v1),
        ("V2 (var names)",         min_subarray_len_v2),
        ("V3 (brute)",             min_subarray_len_v3),
        ("V4 (prefix + bisect)",   min_subarray_len_v4),
        ("V5 (accumulate)",        min_subarray_len_v5),
        ("V6 (numpy)",             min_subarray_len_v6),
        ("V7 (deque)",             min_subarray_len_v7),
        ("V8 (recursive)",         min_subarray_len_v8),
        ("V9 (alt sliding)",       min_subarray_len_v9),
        ("V10 (final clean)",      min_subarray_len_v10),
    ]

    test_cases = [
        # (target, nums, expected)
        (7, [2, 3, 1, 2, 4, 3], 2),
        (4, [1, 4, 4], 1),
        (11, [1, 1, 1, 1, 1, 1, 1, 1], 0),
        (11, [1, 2, 3, 4, 5], 3),
        (15, [1, 2, 3, 4, 5], 5),
        (1, [1], 1),
        (5, [1, 1, 1, 1, 1], 5),
        (5, [5], 1),
        (5, [5, 5, 5], 1),
        (3, [1, 1, 1], 3),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (target, nums, expected) in enumerate(test_cases):
            try:
                got = func(target, nums)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: target={target}, nums={nums} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")