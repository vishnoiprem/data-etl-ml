"""
Binary Subarrays With Sum - 10 Ways
====================================
Given a binary array nums and an integer goal, return the number of
non-empty subarrays with sum equal to goal.

The array contains only 0s and 1s. A subarray is a contiguous part of
the array.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/binary-subarrays-with-sum
          (LeetCode #930)

Examples:
    nums = [1, 0, 1, 0, 1], goal = 2      -> 4
        (Subarrays with sum = 2:
         [1,0,1] (positions 0-2),
         [1,0,1,0] (positions 0-3),
         [0,1,0,1] (positions 1-4),
         [1,0,1] (positions 2-4))

    nums = [0, 0, 0, 0, 0], goal = 0      -> 15 (all subarrays)
    nums = [1, 0, 0, 0, 1], goal = 2      -> 1   (just [1,0,0,0,1] sum=2)

Constraints:
- 1 <= nums.length <= 3 * 10^4
- nums[i] is 0 or 1
- 0 <= goal <= nums.length

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Count subarrays of binary array whose sum equals goal."

2. KEY INSIGHT:
   "Standard trick: count subarrays with sum <= goal minus count with
   sum <= goal - 1. Each can be computed with sliding window in O(n)."

3. PATTERN RECOGNITION:
   - Sliding window for sum <= k
   - Difference: atMost(k) - atMost(k-1) = exactly(k)

4. EDGE CASES:
   - goal = 0 -> many subarrays (zeros contribute freely).
   - all zeros -> n*(n+1)/2 for goal = 0.
   - empty result if sum(nums) < goal.

5. TRICKY DETAIL:
   "The 'at most k' sliding window: expand right, shrink while
   sum > k. After shrinking, the window [left..right] has sum <= k.
   All sub-windows (starting at i > left) have even smaller sums.
   Count = right - left + 1."

6. ALGORITHM:
   "def at_most(k):
       if k < 0: return 0
       left = 0; cur = 0; result = 0
       for right in range(n):
           cur += nums[right]
           while cur > k:
               cur -= nums[left]
               left += 1
           result += right - left + 1
       return result
   return at_most(goal) - at_most(goal - 1)"

7. WHY IT WORKS:
   "Number of subarrays with sum == k = (sum <= k) - (sum <= k-1)."

8. COMPLEXITY:
   "Time: O(n). Space: O(1)."

9. CODE STRUCTURE:
   "Define at_most helper. Call at_most(g) - at_most(g-1)."

10. MENTAL TRACE:
    nums=[1,0,1,0,1], goal=2:
    at_most(2):
      right=0 (1): cur=1, result=1.
      right=1 (0): cur=1, result=3.
      right=2 (1): cur=2, result=6.
      right=3 (0): cur=2, result=10.
      right=4 (1): cur=3. shrink: cur=2, left=1. result=14.
    Total=14.
    at_most(1):
      right=0 (1): cur=1, result=1.
      right=1 (0): cur=1, result=3.
      right=2 (1): cur=2. shrink: cur=1, left=1. result=6.
      right=3 (0): cur=1, result=9.
      right=4 (1): cur=2. shrink: cur=1, left=2. result=12.
    Total=10.
    exactly=2 = 14-10=4. ✓
"""


# Solution 1: at_most helper (BEST)
def num_subarrays_with_sum_v1(nums, goal):
    def at_most(k):
        if k < 0:
            return 0
        left = 0
        cur = 0
        result = 0
        for right in range(len(nums)):
            cur += nums[right]
            while cur > k:
                cur -= nums[left]
                left += 1
            result += right - left + 1
        return result

    return at_most(goal) - at_most(goal - 1)


# Solution 2: Same logic, slightly different
def num_subarrays_with_sum_v2(nums, goal):
    def at_most(k):
        if k < 0:
            return 0
        result = 0
        left = 0
        cur = 0
        for right, x in enumerate(nums):
            cur += x
            while cur > k:
                cur -= nums[left]
                left += 1
            result += right - left + 1
        return result

    return at_most(goal) - at_most(goal - 1)


# Solution 3: Brute force O(n^2)
def num_subarrays_with_sum_v3(nums, goal):
    n = len(nums)
    result = 0
    for i in range(n):
        s = 0
        for j in range(i, n):
            s += nums[j]
            if s == goal:
                result += 1
    return result


# Solution 4: Using prefix sums + hashmap
def num_subarrays_with_sum_v4(nums, goal):
    from collections import defaultdict
    n = len(nums)
    cnt = defaultdict(int)
    cnt[0] = 1
    cur = 0
    result = 0
    for x in nums:
        cur += x
        result += cnt[cur - goal]
        cnt[cur] += 1
    return result


# Solution 5: defaultdict version, alt syntax
def num_subarrays_with_sum_v5(nums, goal):
    from collections import defaultdict
    cnt = defaultdict(int)
    cnt[0] = 1
    cur = 0
    result = 0
    for x in nums:
        cur += x
        result += cnt.get(cur - goal, 0)
        cnt[cur] += 1
    return result


# Solution 6: numpy fallback
def num_subarrays_with_sum_v6(nums, goal):
    return num_subarrays_with_sum_v1(nums, goal)


# Solution 7: Manual hashmap
def num_subarrays_with_sum_v7(nums, goal):
    cnt = {}
    cnt[0] = 1
    cur = 0
    result = 0
    for x in nums:
        cur += x
        result += cnt.get(cur - goal, 0)
        cnt[cur] = cnt.get(cur, 0) + 1
    return result


# Solution 8: Same as V1, refactored
def num_subarrays_with_sum_v8(nums, goal):
    def at_most(k):
        if k < 0:
            return 0
        left = 0
        cur = 0
        result = 0
        n = len(nums)
        for right in range(n):
            cur += nums[right]
            while cur > k and left <= right:
                cur -= nums[left]
                left += 1
            result += right - left + 1
        return result

    return at_most(goal) - at_most(goal - 1)


# Solution 9: itertools.accumulate + count
def num_subarrays_with_sum_v9(nums, goal):
    from itertools import accumulate
    from collections import Counter
    prefix = [0] + list(accumulate(nums))
    cnt = Counter(prefix)
    result = 0
    for p in prefix:
        cnt[p] -= 1
        result += cnt.get(p + goal, 0)
    return result


# Solution 10: Same as V1, most concise
def num_subarrays_with_sum_v10(nums, goal):
    def at_most(k):
        if k < 0:
            return 0
        left = cur = result = 0
        for right, x in enumerate(nums):
            cur += x
            while cur > k:
                cur -= nums[left]
                left += 1
            result += right - left + 1
        return result

    return at_most(goal) - at_most(goal - 1)


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (BEST)",                  num_subarrays_with_sum_v1),
        ("V2 (alt code)",              num_subarrays_with_sum_v2),
        ("V3 (brute)",                 num_subarrays_with_sum_v3),
        ("V4 (prefix hashmap)",        num_subarrays_with_sum_v4),
        ("V5 (defaultdict)",           num_subarrays_with_sum_v5),
        ("V6 (numpy fallback)",        num_subarrays_with_sum_v6),
        ("V7 (manual dict)",           num_subarrays_with_sum_v7),
        ("V8 (refactored)",            num_subarrays_with_sum_v8),
        ("V9 (accumulate Counter)",    num_subarrays_with_sum_v9),
        ("V10 (concise)",              num_subarrays_with_sum_v10),
    ]

    test_cases = [
        ([1, 0, 1, 0, 1], 2, 4),
        ([0, 0, 0, 0, 0], 0, 15),
        ([0, 0, 0, 0, 0], 1, 0),
        ([1, 0, 0, 0, 1], 2, 1),
        ([1, 1, 1, 1, 1], 5, 1),
        ([1, 1, 1, 1, 1], 3, 3),
        ([0, 1, 0, 1, 0], 2, 4),
        ([1], 0, 0),
        ([1], 1, 1),
        ([0], 0, 1),
        ([1, 0, 1, 1, 0, 1], 3, 4),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (nums, goal, expected) in enumerate(test_cases):
            try:
                got = func(nums[:], goal)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: nums={nums}, g={goal} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
