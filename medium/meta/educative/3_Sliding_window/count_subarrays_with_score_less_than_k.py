"""
Count Subarrays With Score Less Than K - 10 Ways
================================================
The score of an array is defined as the product of its sum and length.

Given an integer array nums and an integer k, return the number of
non-empty subarrays whose score is strictly less than k.

The score of a subarray is defined as (sum of subarray elements) *
(length of subarray).

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/count-subarrays-with-score-less-than-k
          (LeetCode #2302)

Examples:
    nums = [2, 1, 4, 3, 5], k = 10      -> 6
        (subarrays with score < 10:
         [2] (2*1=2), [1] (1*1=1), [4] (4*1=4), [3] (3*1=3), [5] (5*1=5),
         [2,1] (3*2=6). Others have score >= 10:
         [4,3] (7*2=14), [1,4] (5*2=10 — equal, not less), etc.)
    nums = [1, 1, 1], k = 5              -> 5
        ([1] x 3, [1,1] x 2 (sum*2=4<5))
        ([1,1,1] score = 9 not less)
    nums = [5, 5, 5], k = 1              -> 0

Constraints:
- 1 <= nums.length <= 10^5
- 1 <= nums[i] <= 10^5
- 1 <= k <= 10^15

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Count subarrays where sum * length < k."

2. KEY INSIGHT:
   "Sliding window with running sum. For each right, find the SMALLEST
    left such that (sum * len) >= k. Then valid windows ending at right
    start in [original_left, smallest_left - 1]."

3. PATTERN RECOGNITION:
   "Sliding window with monotonic property. For each right, count
    valid lefts."

4. EDGE CASES:
   - k <= 0 (not in constraints) -> 0.
   - Single elements with sum >= k -> 0 (those elements).
   - All ones: for k = n+1, count = n*(n+1)/2.

5. TRICKY DETAIL:
   "For fixed right, as left DECREASES (window grows), sum increases
    and length increases, so score INCREASES monotonically. Once
    score >= k for some left, all smaller lefts are invalid too."

6. ALGORITHM:
   "left = 0; cur_sum = 0; result = 0
    for right in range(n):
        cur_sum += nums[right]
        while left <= right and cur_sum * (right - left + 1) >= k:
            cur_sum -= nums[left]
            left += 1
        result += right - left + 1
    return result"

7. WHY IT WORKS:
   "After the while loop, the window [left..right] is the LARGEST
    valid window ending at right (i.e., extending it would make score
    >= k). All windows ending at right starting at any index in
    [left..right] are valid (smaller windows have smaller scores).
    Count is right - left + 1."

8. COMPLEXITY:
   "Time: O(n) - each element added and removed at most once.
    Space: O(1)."

9. CODE STRUCTURE:
   "Initialize left, cur_sum, result. Iterate right. Shrink while
    score too high. Add count."

10. MENTAL TRACE:
    nums = [2, 1, 4, 3, 5], k = 10:
    left=0, cur_sum=0, result=0.
    right=0 (2): cur=2. score=2*1=2 < 10. result += 1. result=1.
    right=1 (1): cur=3. score=3*2=6 < 10. result += 2. result=3.
    right=2 (4): cur=7. score=7*3=21 >= 10. shrink: cur=5, left=1.
      score=5*2=10 >= 10. shrink: cur=4, left=2.
      score=4*1=4 < 10. result += 1. result=4.
    right=3 (3): cur=7. score=7*2=14 >= 10. shrink: cur=3, left=3.
      score=3*1=3 < 10. result += 1. result=5.
    right=4 (5): cur=8. score=8*2=16 >= 10. shrink: cur=5, left=4.
      score=5*1=5 < 10. result += 1. result=6.
    Returns 6. ✓
"""


# Solution 1: Sliding window (BEST)
def count_subarrays_v1(nums, k):
    n = len(nums)
    left = 0
    cur_sum = 0
    result = 0
    for right in range(n):
        cur_sum += nums[right]
        while left <= right and cur_sum * (right - left + 1) >= k:
            cur_sum -= nums[left]
            left += 1
        result += right - left + 1
    return result


# Solution 2: Same logic, slightly different code
def count_subarrays_v2(nums, k):
    n = len(nums)
    left = 0
    cur_sum = 0
    result = 0
    for right in range(n):
        cur_sum += nums[right]
        while cur_sum * (right - left + 1) >= k:
            cur_sum -= nums[left]
            left += 1
        result += right - left + 1
    return result


# Solution 3: Brute force O(n^2)
def count_subarrays_v3(nums, k):
    n = len(nums)
    result = 0
    for i in range(n):
        s = 0
        for j in range(i, n):
            s += nums[j]
            if s * (j - i + 1) < k:
                result += 1
            else:
                break
    return result


# Solution 4: Prefix sums + binary search
def count_subarrays_v4(nums, k):
    n = len(nums)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]
    result = 0
    # For each left, find smallest right such that score >= k
    # score = (prefix[right+1] - prefix[left]) * (right - left + 1)
    # Hard to binary search directly because of (right - left + 1).
    # Alternative: for each right, find smallest left where score < k
    # Score is monotonically decreasing as left increases (window shrinks).
    for right in range(n):
        # Binary search for smallest left where score >= k
        lo, hi = 0, right + 1
        while lo < hi:
            mid = (lo + hi) // 2
            s = prefix[right + 1] - prefix[mid]
            length = right - mid + 1
            if s * length >= k:
                lo = mid + 1
            else:
                hi = mid
        # lo is the smallest left where score < k
        # Valid windows ending at right start at any index in [0, lo-1]
        # Wait, we want smallest left such that score < k. Hmm.
        # Let me re-derive. We want windows starting at left where
        # (sum * len) < k. As left decreases, both sum and len
        # increase, so score increases.
        # So for fixed right, score is monotonic decreasing in left.
        # Find the boundary: smallest left where score < k is `lo`.
        # Hmm, actually if left=0 (longest), score is largest.
        # If left = right (shortest), score = nums[right], smallest.
        # So as left increases, score decreases.
        # We want left such that score < k. The smallest such left is
        # the threshold. All left >= that have score < k.
        # So count valid lefts = right - smallest + 1.
        result += right - lo + 1
    return result


# Solution 5: Recursive
def count_subarrays_v5(nums, k):
    n = len(nums)
    left = [0]
    cur_sum = [0]
    result = [0]

    def helper(right):
        if right == n:
            return
        cur_sum[0] += nums[right]
        while cur_sum[0] * (right - left[0] + 1) >= k:
            cur_sum[0] -= nums[left[0]]
            left[0] += 1
        result[0] += right - left[0] + 1
        helper(right + 1)

    helper(0)
    return result[0]


# Solution 6: itertools.accumulate
def count_subarrays_v6(nums, k):
    from itertools import accumulate
    n = len(nums)
    prefix = [0] + list(accumulate(nums))
    result = 0
    for right in range(n):
        lo, hi = 0, right + 1
        while lo < hi:
            mid = (lo + hi) // 2
            s = prefix[right + 1] - prefix[mid]
            length = right - mid + 1
            if s * length >= k:
                lo = mid + 1
            else:
                hi = mid
        result += right - lo + 1
    return result


# Solution 7: numpy version
def count_subarrays_v7(nums, k):
    try:
        import numpy as np
        # Hard to vectorize; use V1.
        return count_subarrays_v1(nums, k)
    except ImportError:
        return count_subarrays_v1(nums, k)


# Solution 8: Deque-based (overkill)
def count_subarrays_v8(nums, k):
    from collections import deque
    n = len(nums)
    if n == 0:
        return 0
    dq = deque(nums[:1])
    cur_sum = nums[0]
    left = 0
    result = 0
    for right in range(n):
        if right > 0:
            cur_sum += nums[right]
            dq.append(nums[right])
        while cur_sum * (right - left + 1) >= k and dq:
            cur_sum -= dq.popleft()
            left += 1
        result += right - left + 1
    return result


# Solution 9: Iterative with explicit length tracking
def count_subarrays_v9(nums, k):
    n = len(nums)
    left = 0
    cur_sum = 0
    result = 0
    for right in range(n):
        cur_sum += nums[right]
        length = right - left + 1
        while cur_sum * length >= k:
            cur_sum -= nums[left]
            left += 1
            length = right - left + 1
        result += length
    return result


# Solution 10: Final cleanest
def count_subarrays_v10(nums, k):
    left = 0
    cur_sum = 0
    result = 0
    for right, x in enumerate(nums):
        cur_sum += x
        while cur_sum * (right - left + 1) >= k:
            cur_sum -= nums[left]
            left += 1
        result += right - left + 1
    return result


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (BEST)",                  count_subarrays_v1),
        ("V2 (alt code)",              count_subarrays_v2),
        ("V3 (brute)",                 count_subarrays_v3),
        ("V4 (prefix + binsearch)",    count_subarrays_v4),
        ("V5 (recursive)",             count_subarrays_v5),
        ("V6 (accumulate)",            count_subarrays_v6),
        ("V7 (numpy)",                 count_subarrays_v7),
        ("V8 (deque)",                 count_subarrays_v8),
        ("V9 (length tracking)",       count_subarrays_v9),
        ("V10 (final clean)",          count_subarrays_v10),
    ]

    test_cases = [
        # (nums, k, expected)
        ([2, 1, 4, 3, 5], 10, 6),
        ([1, 1, 1], 5, 5),
        ([5, 5, 5], 1, 0),
        ([1, 2, 3, 4, 5], 100, 15),  # all subarrays have score < 100
        ([1, 2, 3, 4, 5], 6, 5),
        ([1, 2, 3, 4, 5], 4, 3),  # [1],[2],[3]
        ([2, 1, 4, 3, 5], 100, 15),
        ([10], 50, 1),
        ([10], 100, 1),
        ([10], 11, 1),  # 10*1 = 10 < 11
        ([10], 9, 0),  # 10*1 = 10 >= 9
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (nums, k, expected) in enumerate(test_cases):
            try:
                got = func(nums[:], k)
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