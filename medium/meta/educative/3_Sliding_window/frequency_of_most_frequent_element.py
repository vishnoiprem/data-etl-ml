"""
Frequency of the Most Frequent Element - 10 Ways
=================================================
You are given an integer array nums and an integer k. In one operation,
you can increment any element of the array by 1 (you can perform this
operation at most k times). That is, the value of nums[i] can be at most
nums[i] + k.

Return the maximum possible frequency of any element after performing
at most k increments.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/frequency-of-most-frequent-element
          (LeetCode #1838)

Examples:
    nums = [1, 2, 4], k = 5               -> 3  (all become 4)
    nums = [1, 4, 8, 13], k = 5           -> 2
    nums = [3, 9, 6], k = 2               -> 1
    nums = [1, 1, 1], k = 0               -> 3

Constraints:
- 1 <= nums.length <= 10^5
- 1 <= nums[i] <= 10^5
- 0 <= k <= 10^5

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Increment at most k elements by 1 each (total k operations). Maximize
    the frequency of any value."

2. KEY INSIGHT:
   "Sort the array. Then sliding window: maintain a window [left, right]
    where we can make all elements in the window equal to nums[right]
    using at most k increments. The total cost is:
    (window_length * nums[right]) - sum(window)."

3. PATTERN RECOGNITION:
   "Sort + sliding window. Track sum of window. Condition:
    window_len * nums[right] - sum <= k."

4. EDGE CASES:
   - k == 0: longest run of equal elements.
   - All same: n.
   - k very large: n.

5. TRICKY DETAIL:
   "We sort the array FIRST. The 'target' value is the rightmost
    element of the window (always the largest). All smaller elements
    must be incremented up to that value. Cost = target * len - sum."

6. ALGORITHM:
   "Sort nums.
    left = 0; cur_sum = 0; best = 0
    for right in range(n):
        cur_sum += nums[right]
        while nums[right] * (right - left + 1) - cur_sum > k:
            cur_sum -= nums[left]
            left += 1
        best = max(best, right - left + 1)
    return best"

7. WHY IT WORKS:
   "After sorting, we have a non-decreasing array. The rightmost
    element is always the largest. Making all elements in window
    equal to nums[right] requires total increments =
    nums[right] * len - sum. We track max window where this <= k."

8. COMPLEXITY:
   "Time: O(n log n) for sort + O(n) for the sliding window.
    Space: O(1) or O(n) depending on sort."

9. CODE STRUCTURE:
   "Sort. Iterate right. While window too expensive, shrink left.
    Update best."

10. MENTAL TRACE:
    nums = [1, 4, 8, 13], k = 5:
    Sort: [1, 4, 8, 13].
    left=0, sum=0, best=0.
    right=0 (1): sum=1. cost = 1*1 - 1 = 0 <= 5. best=1.
    right=1 (4): sum=5. cost = 4*2 - 5 = 3 <= 5. best=2.
    right=2 (8): sum=13. cost = 8*3 - 13 = 11 > 5. shrink:
      left=0 (1), sum=12. cost = 8*2 - 12 = 4. best=2.
    right=3 (13): sum=25. cost = 13*2 - 25 = 1. best=2.
    Returns 2. ✓
"""


# Solution 1: Sort + sliding window (BEST)
def max_frequency_v1(nums, k):
    nums.sort()
    left = 0
    cur_sum = 0
    best = 0
    for right in range(len(nums)):
        cur_sum += nums[right]
        # Cost to make all in window equal to nums[right]:
        # nums[right] * len - sum
        while nums[right] * (right - left + 1) - cur_sum > k:
            cur_sum -= nums[left]
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 2: Sort + sliding window with prefix sums and binary search
def max_frequency_v2(nums, k):
    nums.sort()
    n = len(nums)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]
    best = 0
    # For each right, find the smallest left such that cost <= k.
    # Use two-pointer instead of binary search for clarity.
    left = 0
    for right in range(n):
        while left <= right:
            cost = nums[right] * (right - left + 1) - (prefix[right + 1] - prefix[left])
            if cost <= k:
                break
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 3: Sort + sliding window (cleaner code)
def max_frequency_v3(nums, k):
    nums.sort()
    left = 0
    cur_sum = 0
    best = 0
    for right in range(len(nums)):
        cur_sum += nums[right]
        target = nums[right]
        window_len = right - left + 1
        cost = target * window_len - cur_sum
        while cost > k:
            cur_sum -= nums[left]
            left += 1
            window_len = right - left + 1
            cost = target * window_len - cur_sum
        if window_len > best:
            best = window_len
    return best


# Solution 4: Sort + brute force (O(n^2))
def max_frequency_v4(nums, k):
    nums.sort()
    n = len(nums)
    best = 1
    for right in range(n):
        # Find leftmost window ending at right where cost <= k
        cost = 0
        left = right
        for L in range(right, -1, -1):
            cost += nums[right] - nums[L]
            if cost > k:
                break
            left = L
        # Window = [left..right], length = right - left + 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 5: Use deque or heap (over-engineered)
def max_frequency_v5(nums, k):
    # Same as V1 just using different loop
    nums.sort()
    left = 0
    cur_sum = 0
    best = 0
    for right in range(len(nums)):
        cur_sum += nums[right]
        # Shrink if too expensive
        if nums[right] * (right - left + 1) - cur_sum > k:
            # Shrink until valid
            while nums[right] * (right - left + 1) - cur_sum > k:
                cur_sum -= nums[left]
                left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 6: Sort + sliding window with explicit target tracking
def max_frequency_v6(nums, k):
    nums.sort()
    n = len(nums)
    left = 0
    cur_sum = 0
    best = 0
    target = 0
    for right in range(n):
        cur_sum += nums[right]
        target = nums[right]
        # Try to expand window
        while left <= right and target * (right - left + 1) - cur_sum > k:
            cur_sum -= nums[left]
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 7: Sort + sliding window (alternate impl)
def max_frequency_v7(nums, k):
    nums.sort()
    n = len(nums)
    left = 0
    cur_sum = 0
    best = 0
    for right in range(n):
        cur_sum += nums[right]
        target = nums[right]
        window_len = right - left + 1
        while target * window_len - cur_sum > k:
            cur_sum -= nums[left]
            left += 1
            window_len = right - left + 1
        if window_len > best:
            best = window_len
    return best


# Solution 8: itertools.accumulate for prefix sums
def max_frequency_v8(nums, k):
    from itertools import accumulate
    nums.sort()
    n = len(nums)
    prefix = [0] + list(accumulate(nums))
    best = 0
    left = 0
    for right in range(n):
        while left <= right:
            cost = nums[right] * (right - left + 1) - (prefix[right + 1] - prefix[left])
            if cost <= k:
                break
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 9: Recursive
def max_frequency_v9(nums, k):
    nums = sorted(nums)
    n = len(nums)
    state = {"left": 0, "cur_sum": 0, "best": 0}

    def helper(right):
        if right == n:
            return
        state["cur_sum"] += nums[right]
        while nums[right] * (right - state["left"] + 1) - state["cur_sum"] > k:
            state["cur_sum"] -= nums[state["left"]]
            state["left"] += 1
        if right - state["left"] + 1 > state["best"]:
            state["best"] = right - state["left"] + 1
        helper(right + 1)

    helper(0)
    return state["best"]


# Solution 10: numpy version
def max_frequency_v10(nums, k):
    try:
        import numpy as np
        nums = sorted(nums)
        arr = np.array(nums)
        prefix = np.zeros(len(arr) + 1)
        prefix[1:] = np.cumsum(arr)
        best = 0
        left = 0
        for right in range(len(arr)):
            while left <= right:
                cost = arr[right] * (right - left + 1) - (prefix[right + 1] - prefix[left])
                if cost <= k:
                    break
                left += 1
            if right - left + 1 > best:
                best = right - left + 1
        return int(best)
    except ImportError:
        return max_frequency_v1(nums, k)


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (BEST)",                       max_frequency_v1),
        ("V2 (binary search)",              max_frequency_v2),
        ("V3 (clean code)",                 max_frequency_v3),
        ("V4 (brute inner)",                max_frequency_v4),
        ("V5 (same V1 logic)",              max_frequency_v5),
        ("V6 (explicit target)",            max_frequency_v6),
        ("V7 (heap variant)",               max_frequency_v7),
        ("V8 (accumulate)",                 max_frequency_v8),
        ("V9 (recursive)",                  max_frequency_v9),
        ("V10 (numpy)",                     max_frequency_v10),
    ]

    test_cases = [
        # (nums, k, expected)
        ([1, 2, 4], 5, 3),
        ([1, 4, 8, 13], 5, 2),
        ([3, 9, 6], 2, 1),
        ([1, 1, 1], 0, 3),
        ([5, 5, 5, 5], 1, 4),
        ([10], 0, 1),
        ([1, 2, 3, 4, 5], 100, 5),
        ([1, 1, 2, 2, 3, 3], 3, 4),
        ([1, 1, 3, 3, 3, 5, 5, 5, 5, 7], 1, 4),
        ([1, 10, 100], 0, 1),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (nums, k, expected) in enumerate(test_cases):
            try:
                got = func(nums[:], k)  # pass copy since V1 sorts in place
                if got != expected:
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