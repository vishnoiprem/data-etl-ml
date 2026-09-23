"""
Maximum Average Subarray I - 10 Ways
====================================
You are given an integer array nums of length n and an integer k.

Find a contiguous subarray whose length is at least k and at most k,
i.e., exactly k, that has the maximum average value. Return this
average value.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/maximum-average-subarray-i
          (LeetCode #643)

Examples:
    nums = [1, 12, -5, -6, 50, 3], k = 4   -> 12.75
                                              (subarray [12,-5,-6,50])
    nums = [5], k = 1                       -> 5.0
    nums = [0, 1, 1, 3, 3], k = 4           -> 2.0
                                              (subarray [1,1,3,3])

Constraints:
- n == nums.length
- 1 <= n <= 10^5
- -10^4 <= nums[i] <= 10^4
- 1 <= k <= n

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Find the maximum average of any contiguous subarray of length EXACTLY k."

2. KEY INSIGHT:
   "Sliding window of size k. Track running sum. Max sum = max average."

3. PATTERN RECOGNITION:
   "Fixed-size sliding window. Maintain sum; subtract left, add right."

4. EDGE CASES:
   - k == n -> average of all.
   - k == 1 -> max element.
   - All negative: largest (least negative) k consecutive.

5. TRICKY DETAIL:
   "We slide a WINDOW of EXACT size k. At each step, the window's sum
    divided by k gives the average. Track the max sum."

6. ALGORITHM:
   "cur = sum(nums[0..k-1])
    best = cur
    for i in range(k, n):
        cur += nums[i] - nums[i - k]
        if cur > best: best = cur
    return best / k"

7. WHY IT WORKS:
   "Each window of size k has a unique sum. The maximum sum corresponds
    to the maximum average (since the divisor k is constant)."

8. COMPLEXITY:
   "Time: O(n) - one pass.
    Space: O(1)."

9. CODE STRUCTURE:
   "Compute initial sum of first k elements. Slide window, updating sum.
    Track max sum. Return max_sum / k."

10. MENTAL TRACE:
    nums = [1, 12, -5, -6, 50, 3], k = 4:
    Initial sum = 1 + 12 + (-5) + (-6) = 2. best = 2.
    i=4 (50): cur = 2 + 50 - 1 = 51. best = 51.
    i=5 (3): cur = 51 + 3 - 12 = 42. best = 51.
    max avg = 51 / 4 = 12.75. ✓
"""


# Solution 1: Fixed-size sliding window (BEST)
def find_max_average_v1(nums, k):
    n = len(nums)
    cur = sum(nums[:k])
    best = cur
    for i in range(k, n):
        cur += nums[i] - nums[i - k]
        if cur > best:
            best = cur
    return best / k


# Solution 2: Same logic, alternative form
def find_max_average_v2(nums, k):
    n = len(nums)
    cur = sum(nums[:k])
    best = cur
    for i in range(k, n):
        cur = cur + nums[i] - nums[i - k]
        best = max(best, cur)
    return best / k


# Solution 3: Brute force O(n*k)
def find_max_average_v3(nums, k):
    n = len(nums)
    best = float('-inf')
    for i in range(n - k + 1):
        s = sum(nums[i:i + k])
        if s > best:
            best = s
    return best / k


# Solution 4: Prefix sums
def find_max_average_v4(nums, k):
    n = len(nums)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]
    best = float('-inf')
    for i in range(k, n + 1):
        s = prefix[i] - prefix[i - k]
        if s > best:
            best = s
    return best / k


# Solution 5: itertools.accumulate + slices
def find_max_average_v5(nums, k):
    from itertools import accumulate
    n = len(nums)
    prefix = [0] + list(accumulate(nums))
    best = float('-inf')
    for i in range(k, n + 1):
        s = prefix[i] - prefix[i - k]
        if s > best:
            best = s
    return best / k


# Solution 6: numpy sliding window
def find_max_average_v6(nums, k):
    try:
        import numpy as np
        arr = np.array(nums)
        from numpy.lib.stride_tricks import sliding_window_view
        windows = sliding_window_view(arr, k)
        sums = windows.sum(axis=1)
        return float(sums.max()) / k
    except (ImportError, AttributeError):
        return find_max_average_v1(nums, k)


# Solution 7: Deque-based sliding window (over-engineered)
def find_max_average_v7(nums, k):
    from collections import deque
    n = len(nums)
    if k == n:
        return sum(nums) / k
    dq = deque(nums[:k])
    cur = sum(nums[:k])
    best = cur
    for i in range(k, n):
        cur += nums[i] - dq.popleft()
        dq.append(nums[i])
        if cur > best:
            best = cur
    return best / k


# Solution 8: Sliding window with manual array
def find_max_average_v8(nums, k):
    n = len(nums)
    window = nums[:k]
    cur = sum(window)
    best = cur
    for i in range(k, n):
        window = window[1:] + [nums[i]]
        cur = sum(window)
        if cur > best:
            best = cur
    return best / k


# Solution 9: Recursive
def find_max_average_v9(nums, k):
    n = len(nums)
    cur = [sum(nums[:k])]
    best = [cur[0]]

    def helper(i):
        if i == n:
            return
        cur[0] += nums[i] - nums[i - k]
        if cur[0] > best[0]:
            best[0] = cur[0]
        helper(i + 1)

    helper(k)
    return best[0] / k


# Solution 10: Final cleanest
def find_max_average_v10(nums, k):
    cur = sum(nums[:k])
    best = cur
    for i in range(k, len(nums)):
        cur += nums[i] - nums[i - k]
        best = max(best, cur)
    return best / k


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (BEST)",                  find_max_average_v1),
        ("V2 (alt form)",              find_max_average_v2),
        ("V3 (brute)",                 find_max_average_v3),
        ("V4 (prefix sum)",            find_max_average_v4),
        ("V5 (accumulate)",            find_max_average_v5),
        ("V6 (numpy)",                 find_max_average_v6),
        ("V7 (deque)",                 find_max_average_v7),
        ("V8 (manual window)",         find_max_average_v8),
        ("V9 (recursive)",             find_max_average_v9),
        ("V10 (final clean)",          find_max_average_v10),
    ]

    test_cases = [
        # (nums, k, expected)
        ([1, 12, -5, -6, 50, 3], 4, 12.75),
        ([5], 1, 5.0),
        ([0, 1, 1, 3, 3], 4, 2.0),
        ([1, 2, 3, 4, 5], 1, 5.0),  # max element
        ([1, 2, 3, 4, 5], 5, 3.0),  # average of all
        ([-1, -2, -3, -4], 2, -1.5),  # [-1, -2] is -1.5
        ([4, 0, 0, 0, 0, 0], 5, 0.8),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (nums, k, expected) in enumerate(test_cases):
            try:
                got = func(nums[:], k)  # copy to avoid mutation
                if abs(got - expected) > 1e-9:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: nums={nums}, k={k} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")