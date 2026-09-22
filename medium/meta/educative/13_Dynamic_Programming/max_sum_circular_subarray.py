"""
Maximum Sum Circular Subarray - 20 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/maximum-sum-circular-subarray

Given a circular integer array nums, find the maximum sum of a non-empty
subarray. The subarray can wrap around (end to beginning).

KEY INSIGHT:
For non-circular: Kadane's algorithm gives max subarray sum in O(n).
For circular: two cases:
1. Maximum subarray doesn't wrap: use Kadane's.
2. Maximum subarray wraps: equivalent to total_sum - min_subarray_sum
   (the wrapped part is total - non-wrapped part, and we want to MINIMIZE
   the non-wrapped part to MAXIMIZE the wrapped part).

Answer = max(kadane_max, total_sum - kadane_min)
But edge case: if all numbers are negative, the wrapped case gives 0 (empty),
so we should return kadane_max in that case.

Examples:
    nums=[1,-2,3,-2] -> 3 (subarray [3])
    nums=[5,-3,5] -> 10 (wrap: [5,5])
    nums=[-3,-2,-3] -> -2 (no wrap, just max single)

Constraints:
- 1 <= n <= 3 * 10^4
- -3 * 10^4 <= nums[i] <= 3 * 10^4
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: Kadane's max + min (BEST - Memorize!)
# ============================================================
def maxSubarraySumCircular_1(nums):
    total = sum(nums)
    # Kadane's for max
    max_ending = max_sofar = nums[0]
    # Kadane's for min
    min_ending = min_sofar = nums[0]

    for i in range(1, len(nums)):
        x = nums[i]
        max_ending = max(x, max_ending + x)
        max_sofar = max(max_sofar, max_ending)

        min_ending = min(x, min_ending + x)
        min_sofar = min(min_sofar, min_ending)

    # If all numbers negative, max_sofar is the answer
    if max_sofar < 0:
        return max_sofar
    return max(max_sofar, total - min_sofar)


# ============================================================
# Way 2: Verbose
# ============================================================
def maxSubarraySumCircular_2(nums):
    n = len(nums)
    total = sum(nums)

    # Kadane's max (non-wrapping)
    dp_max = [0] * n
    dp_max[0] = nums[0]
    for i in range(1, n):
        dp_max[i] = max(nums[i], dp_max[i - 1] + nums[i])
    max_no_wrap = max(dp_max)

    # Kadane's min (for wrap)
    dp_min = [0] * n
    dp_min[0] = nums[0]
    for i in range(1, n):
        dp_min[i] = min(nums[i], dp_min[i - 1] + nums[i])
    min_no_wrap = min(dp_min)

    if max_no_wrap < 0:
        return max_no_wrap
    return max(max_no_wrap, total - min_no_wrap)


# ============================================================
# Way 3: Kadane's applied twice (concise)
# ============================================================
def maxSubarraySumCircular_3(nums):
    def kadane(arr, find_max=True):
        if find_max:
            best = cur = arr[0]
            for x in arr[1:]:
                cur = max(x, cur + x)
                best = max(best, cur)
            return best
        else:
            best = cur = arr[0]
            for x in arr[1:]:
                cur = min(x, cur + x)
                best = min(best, cur)
            return best

    total = sum(nums)
    max_no_wrap = kadane(nums, find_max=True)
    min_no_wrap = kadane(nums, find_max=False)
    if max_no_wrap < 0:
        return max_no_wrap
    return max(max_no_wrap, total - min_no_wrap)


# ============================================================
# Way 4: Brute force (try all subarrays including wraps) - O(n^2)
# ============================================================
def maxSubarraySumCircular_4(nums):
    n = len(nums)
    if n == 1:
        return nums[0]
    best = float('-inf')
    # For each starting index, for each length from 1 to n
    for start in range(n):
        current = 0
        for length in range(1, n + 1):
            current += nums[(start + length - 1) % n]
            best = max(best, current)
    return best


# ============================================================
# Way 5: Doubled array trick (Kadane on 2n array, length <= n)
# ============================================================
def maxSubarraySumCircular_5(nums):
    n = len(nums)
    # Duplicate the array
    doubled = nums + nums
    # Find max subarray of length <= n in doubled array
    best = float('-inf')
    current = 0
    for i in range(len(doubled)):
        current = max(doubled[i], current + doubled[i])
        best = max(best, current)
        # If we've used n+1 elements, reset
        # actually need to track window length
    # This approach needs window tracking - use prefix sums
    prefix = [0]
    for x in doubled:
        prefix.append(prefix[-1] + x)

    # max sum of subarray of length 1..n
    # for each ending position i, find min prefix in [i-n..i-1]
    from collections import deque
    min_deque = deque()
    min_deque.append(0)  # prefix[0] = 0
    best = float('-inf')
    for i in range(1, len(prefix)):
        # window: prefix[i-n..i-1]
        window_start = max(0, i - n)
        while min_deque and min_deque[0] < window_start:
            min_deque.popleft()
        if i - 1 >= 1:
            while min_deque and prefix[i - 1] < prefix[min_deque[-1]]:
                min_deque.pop()
            min_deque.append(i - 1)
        if min_deque:
            best = max(best, prefix[i] - prefix[min_deque[0]])
    return best


# ============================================================
# Way 6: Class-based
# ============================================================
class MaxSumCircularSubarray_6:
    def __init__(self, nums):
        self.nums = nums

    def compute(self):
        total = sum(self.nums)
        max_ending = max_sofar = self.nums[0]
        min_ending = min_sofar = self.nums[0]

        for i in range(1, len(self.nums)):
            x = self.nums[i]
            max_ending = max(x, max_ending + x)
            max_sofar = max(max_sofar, max_ending)

            min_ending = min(x, min_ending + x)
            min_sofar = min(min_sofar, min_ending)

        if max_sofar < 0:
            return max_sofar
        return max(max_sofar, total - min_sofar)


def maxSubarraySumCircular_6(nums):
    return MaxSumCircularSubarray_6(nums).compute()


# ============================================================
# Way 7: numpy vectorized
# ============================================================
def maxSubarraySumCircular_7(nums):
    import numpy as np
    arr = np.array(nums)
    n = len(arr)
    total = arr.sum()

    # Kadane's for max
    max_ending = arr.copy()
    for i in range(1, n):
        max_ending[i] = np.maximum(arr[i], max_ending[i - 1] + arr[i])
    max_no_wrap = max_ending.max()

    # Kadane's for min
    min_ending = arr.copy()
    for i in range(1, n):
        min_ending[i] = np.minimum(arr[i], min_ending[i - 1] + arr[i])
    min_no_wrap = min_ending.min()

    if max_no_wrap < 0:
        return int(max_no_wrap)
    return int(max(max_no_wrap, total - min_no_wrap))


# ============================================================
# Way 8: lru_cache for memoized recursion
# ============================================================
from functools import lru_cache


def maxSubarraySumCircular_8(nums):
    # Use DP: max subarray ending at i (no wrap), max subarray starting at i (no wrap)
    # For wrap, we can split into prefix + suffix where neither is empty
    n = len(nums)
    if n == 1:
        return nums[0]

    # max subarray ending at i (no wrap)
    end_at = [0] * n
    end_at[0] = nums[0]
    for i in range(1, n):
        end_at[i] = max(nums[i], end_at[i - 1] + nums[i])

    # max subarray starting at i (no wrap)
    start_at = [0] * n
    start_at[n - 1] = nums[n - 1]
    for i in range(n - 2, -1, -1):
        start_at[i] = max(nums[i], start_at[i + 1] + nums[i])

    # max non-wrap is max(end_at)
    max_no_wrap = max(end_at)

    # max wrap = max over i (end_at[i] + start_at[i+1]) for i in [0..n-2]
    max_wrap = max(end_at[i] + start_at[i + 1] for i in range(n - 1))

    return max(max_no_wrap, max_wrap)


# ============================================================
# Way 9: Helper function extraction
# ============================================================
def maxSubarraySumCircular_9(nums):
    def kadane_max(arr):
        best = cur = arr[0]
        for x in arr[1:]:
            cur = max(x, cur + x)
            best = max(best, cur)
        return best

    def kadane_min(arr):
        best = cur = arr[0]
        for x in arr[1:]:
            cur = min(x, cur + x)
            best = min(best, cur)
        return best

    total = sum(nums)
    max_nw = kadane_max(nums)
    if max_nw < 0:
        return max_nw
    return max(max_nw, total - kadane_min(nums))


# ============================================================
# Way 10: Functional with reduce
# ============================================================
def maxSubarraySumCircular_10(nums):
    from functools import reduce

    def kadane_step(state, x):
        cur_max, best_max, cur_min, best_min = state
        cur_max = max(x, cur_max + x)
        best_max = max(best_max, cur_max)
        cur_min = min(x, cur_min + x)
        best_min = min(best_min, cur_min)
        return (cur_max, best_max, cur_min, best_min)

    init = (nums[0], nums[0], nums[0], nums[0])
    _, max_nw, _, min_nw = reduce(kadane_step, nums[1:], init)

    if max_nw < 0:
        return max_nw
    return max(max_nw, sum(nums) - min_nw)


# ============================================================
# Way 11: One-liner style
# ============================================================
def maxSubarraySumCircular_11(nums):
    total = sum(nums)
    # Compute max and min in one pass using Pythonic style
    def k(xs, op):
        cur = best = xs[0]
        for x in xs[1:]:
            cur = op(x, cur + x)
            best = op(best, cur)
        return best

    mx, mn = k(nums, max), k(nums, min)
    return mx if mx < 0 else max(mx, total - mn)


# ============================================================
# Way 12: Itertools approach (sliding window of size n)
# ============================================================
def maxSubarraySumCircular_12(nums):
    # For each window starting at i, length n, find max subarray
    n = len(nums)
    if n == 1:
        return nums[0]

    from itertools import accumulate
    # Try each starting index
    best = float('-inf')
    for start in range(n):
        # Get subarray [start..start+n-1] circular
        window = [nums[(start + i) % n] for i in range(n)]
        # Apply Kadane
        cur = best_so_far = window[0]
        for x in window[1:]:
            cur = max(x, cur + x)
            best_so_far = max(best_so_far, cur)
        best = max(best, best_so_far)
    return best


# ============================================================
# Way 13: Prefix sums with deque
# ============================================================
def maxSubarraySumCircular_13(nums):
    n = len(nums)
    if n == 1:
        return nums[0]

    # Find max subarray of length 1..n in doubled array using prefix sums
    doubled = nums + nums
    prefix = [0]
    for x in doubled:
        prefix.append(prefix[-1] + x)

    from collections import deque
    dq = deque([0])
    best = float('-inf')

    for i in range(1, len(prefix)):
        # window: prefix[i-n..i-1]
        # remove indices out of window
        while dq and dq[0] < i - n:
            dq.popleft()
        # maintain monotonic increasing deque
        while dq and prefix[i - 1] <= prefix[dq[-1]]:
            dq.pop()
        if i - 1 >= 1:
            dq.append(i - 1)
        elif i - 1 == 0:
            dq.appendleft(0)
        else:
            pass
        # compute candidate
        if dq:
            best = max(best, prefix[i] - prefix[dq[0]])

    return best


# ============================================================
# Way 14: Divide and conquer (less efficient but illustrative)
# ============================================================
def maxSubarraySumCircular_14(nums):
    n = len(nums)
    if n == 1:
        return nums[0]

    def max_subarray(arr, lo, hi):
        if lo == hi:
            return arr[lo]
        mid = (lo + hi) // 2
        # max in left, right, or crossing
        left_max = max_subarray(arr, lo, mid)
        right_max = max_subarray(arr, mid + 1, hi)

        # crossing: max suffix of left + max prefix of right
        left_suffix = arr[mid]
        cur = arr[mid]
        for i in range(mid - 1, lo - 1, -1):
            cur += arr[i]
            left_suffix = max(left_suffix, cur)

        right_prefix = arr[mid + 1]
        cur = arr[mid + 1]
        for i in range(mid + 2, hi + 1):
            cur += arr[i]
            right_prefix = max(right_prefix, cur)

        return max(left_max, right_max, left_suffix + right_prefix)

    # For circular: max is max of (max subarray, total - min subarray)
    def max_sub(arr):
        return max_subarray(arr, 0, len(arr) - 1)

    def min_sub(arr):
        return -max_sub([-x for x in arr])

    total = sum(nums)
    max_nw = max_sub(nums)
    if max_nw < 0:
        return max_nw
    return max(max_nw, total - min_sub(nums))


# ============================================================
# Way 15: enumerate + running sum
# ============================================================
def maxSubarraySumCircular_15(nums):
    total = sum(nums)
    # max subarray
    max_ending = max_sofar = nums[0]
    min_ending = min_sofar = nums[0]
    for i, x in enumerate(nums[1:], 1):
        max_ending = max(x, max_ending + x)
        max_sofar = max(max_sofar, max_ending)
        min_ending = min(x, min_ending + x)
        min_sofar = min(min_sofar, min_ending)
    return max_sofar if max_sofar < 0 else max(max_sofar, total - min_sofar)


# ============================================================
# Way 16: Single pass inline
# ============================================================
def maxSubarraySumCircular_16(nums):
    total = 0
    max_e = max_s = nums[0]
    min_e = min_s = nums[0]
    for x in nums:
        max_e = max(x, max_e + x)
        max_s = max(max_s, max_e)
        min_e = min(x, min_e + x)
        min_s = min(min_s, min_e)
        total += x
    return max_s if max_s < 0 else max(max_s, total - min_s)


# ============================================================
# Way 17: Using itertools.accumulate
# ============================================================
def maxSubarraySumCircular_17(nums):
    from itertools import accumulate
    n = len(nums)
    if n == 1:
        return nums[0]

    # Try all subarrays starting at 0, length 1..n
    # Use prefix sums to compute sums quickly
    # For wrap, try all pairs (i, j) where j is "wrapped" end
    best = float('-inf')
    for start in range(n):
        current = 0
        for length in range(1, n + 1):
            current += nums[(start + length - 1) % n]
            best = max(best, current)
    return best


# ============================================================
# Way 18: Tail recursive (with trampolining via accumulator)
# ============================================================
def maxSubarraySumCircular_18(nums):
    n = len(nums)
    total = 0

    # Iterative: compute max and min using running values
    max_ending_here = 0
    max_sofar = float('-inf')
    min_ending_here = 0
    min_sofar = float('inf')

    for x in nums:
        total += x
        max_ending_here = x if max_ending_here < 0 else max_ending_here + x
        max_sofar = max(max_sofar, max_ending_here)
        min_ending_here = x if min_ending_here > 0 else min_ending_here + x
        min_sofar = min(min_sofar, min_ending_here)

    return max_sofar if max_sofar < 0 else max(max_sofar, total - min_sofar)


# ============================================================
# Way 19: Using deque for max subarray length <= n in doubled
# ============================================================
def maxSubarraySumCircular_19(nums):
    from collections import deque
    n = len(nums)
    if n == 1:
        return nums[0]

    # Build prefix sums of doubled array
    doubled = nums + nums
    prefix = [0]
    for x in doubled:
        prefix.append(prefix[-1] + x)

    # Use deque to find max prefix[i] - prefix[j] where i - j in [1, n]
    dq = deque()
    best = float('-inf')

    for i in range(len(prefix)):
        # i - j in [1, n], so j in [i - n, i - 1]
        # before adding i to dq, compute answers with i as ending
        while dq and dq[0] < i - n:
            dq.popleft()
        if dq:
            best = max(best, prefix[i] - prefix[dq[0]])
        # add i to dq, maintaining min
        while dq and prefix[dq[-1]] >= prefix[i]:
            dq.pop()
        dq.append(i)

    return best


# ============================================================
# Way 20: Final cleanest (the one to memorize)
# ============================================================
def maxSubarraySumCircular_20(nums):
    total = sum(nums)
    cur_max = best_max = nums[0]
    cur_min = best_min = nums[0]
    for x in nums[1:]:
        cur_max = max(x, cur_max + x)
        best_max = max(best_max, cur_max)
        cur_min = min(x, cur_min + x)
        best_min = min(best_min, cur_min)
    return best_max if best_max < 0 else max(best_max, total - best_min)


# ============================================================
# HOW TO THINK (Framework)
# ============================================================
"""
HOW TO THINK ABOUT THIS PROBLEM:

1. UNDERSTAND THE CIRCULAR NATURE:
   - Subarray can wrap: from late index back to early index.
   - Each element included at most once.

2. TWO CASES:
   - Case 1: max subarray doesn't wrap. Use Kadane's.
   - Case 2: max subarray wraps.
     Equivalent to: total_sum - (min subarray that doesn't wrap).
     The wrapped subarray uses everything EXCEPT some middle portion.
     To MAXIMIZE the wrapped portion, we MINIMIZE the non-wrapped portion.

3. ALGORITHM:
   - Compute max_no_wrap = Kadane's max subarray.
   - Compute min_no_wrap = Kadane's min subarray.
   - max_wrap = total - min_no_wrap.
   - Answer = max(max_no_wrap, max_wrap).

4. EDGE CASE:
   - If all numbers are negative: min_no_wrap = total, so max_wrap = 0
     (empty wrap). We should NOT pick empty. Return max_no_wrap (which
     is the largest single negative number).
   - Equivalent check: if max_no_wrap < 0, return max_no_wrap directly.

5. KADANE'S ALGORITHM:
   - cur = max ending at i (can be just x or extend previous).
   - best = max of all cur values.
   - O(n) time.

6. COMPLEXITY:
   - Time: O(n) - single pass with Kadane's twice.
   - Space: O(1).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        # (nums, expected, description)
        ([1, -2, 3, -2], 3, "Standard"),
        ([5, -3, 5], 10, "Wrap: [5,5]"),
        ([-3, -2, -3], -2, "All negative"),
        ([1], 1, "Single positive"),
        ([-1], -1, "Single negative"),
        ([0, 0, 0], 0, "All zeros"),
        ([3, -1, 2, -1], 4, "Standard 2"),
        ([1, 2, 3, 4, 5], 15, "All positive"),
        ([-1, -2, -3, -4], -1, "All negative ascending"),
        ([5, -2, 5], 8, "Wrap partial"),
        ([2, -2, 2, -2, 2], 4, "Alternating"),
        ([8, -1, 3, 4], 15, "Wrap: [3,4,8]"),
        ([1, -2, 3, -2, 4], 5, "Wrap example"),
    ]

    implementations = [
        ("Way 1: Kadane max+min (BEST)", maxSubarraySumCircular_1),
        ("Way 2: Verbose", maxSubarraySumCircular_2),
        ("Way 3: Kadane twice", maxSubarraySumCircular_3),
        ("Way 4: Brute force", maxSubarraySumCircular_4),
        ("Way 5: Doubled array", maxSubarraySumCircular_5),
        ("Way 6: Class-based", maxSubarraySumCircular_6),
        ("Way 7: numpy", maxSubarraySumCircular_7),
        ("Way 8: DP end/start", maxSubarraySumCircular_8),
        ("Way 9: Helper functions", maxSubarraySumCircular_9),
        ("Way 10: Functional reduce", maxSubarraySumCircular_10),
        ("Way 11: One-liner style", maxSubarraySumCircular_11),
        ("Way 12: itertools sliding", maxSubarraySumCircular_12),
        ("Way 13: Deque prefix", maxSubarraySumCircular_13),
        ("Way 14: Divide and conquer", maxSubarraySumCircular_14),
        ("Way 15: enumerate + running", maxSubarraySumCircular_15),
        ("Way 16: Single pass inline", maxSubarraySumCircular_16),
        ("Way 17: accumulate", maxSubarraySumCircular_17),
        ("Way 18: Tail-recursive style", maxSubarraySumCircular_18),
        ("Way 19: Deque max length n", maxSubarraySumCircular_19),
        ("Way 20: Final cleanest", maxSubarraySumCircular_20),
    ]

    for name, fn in implementations:
        passed = 0
        failed = 0
        for nums, expected, desc in test_cases:
            try:
                nums_copy = copy.deepcopy(nums)
                result = fn(nums_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    print(f"  FAIL [{name}] {desc}: nums={nums} expected={expected} got={result}")
            except Exception as e:
                failed += 1
                print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_tests()
