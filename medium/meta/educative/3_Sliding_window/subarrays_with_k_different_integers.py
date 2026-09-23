"""
Subarrays with K Different Integers - 10 Ways
=============================================
Given an integer array nums and an integer k, return the number of
good subarrays of nums.

A good array is an array where the number of distinct integers in the
subarray is exactly k.

For example, [1,2,3,1,2] has 3 distinct integers: 1, 2, and 3.

Return the number of good subarrays of nums.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/subarrays-with-k-different-integers
          (LeetCode #992)

Examples:
    nums = [1, 2, 1, 2, 3], k = 2      -> 7
        (Subarrays with exactly 2 distinct: [1,2], [2,1], [1,2],
         [2,3], [1,2,1], [2,1,2], [1,2,1,2])
    nums = [1, 2, 1, 3, 4], k = 3      -> 4
        (Subarrays with exactly 3 distinct)
    nums = [1, 2, 1, 1, 3], k = 3      -> 3

Constraints:
- 1 <= nums.length <= 2 * 10^4
- 1 <= nums[i] <= nums.length
- 1 <= k <= nums.length

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Count subarrays with EXACTLY k distinct integers."

2. KEY INSIGHT:
   "Exactly k = At most k - At most (k-1). Use sliding window for each."

3. PATTERN RECOGNITION:
   "Count subarrays with at most K distinct. Subtract for exactly K."

4. EDGE CASES:
   - k > distinct_count(nums) -> 0.
   - k == 1 -> only subarrays of single type.

5. TRICKY DETAIL:
   "For each 'right', the number of valid windows ending at 'right'
    is (right - left + 1) after shrinking left to keep at most k
    distinct."

6. ALGORITHM:
   "def at_most(k):
       cnt = Counter()
       left = 0; result = 0
       for right in range(n):
           cnt[nums[right]] += 1
           while len(cnt) > k:
               cnt[nums[left]] -= 1
               if cnt[nums[left]] == 0: del cnt[nums[left]]
               left += 1
           result += right - left + 1
       return result
   return at_most(k) - at_most(k - 1)"

7. WHY IT WORKS:
   "For each right, after shrinking left, the window [left..right]
    has at most k distinct. Any subarray ending at right with start
    in [left..right] has at most k distinct. There are (right-left+1)
    such starts. Summing gives total subarrays with at most k distinct."

8. COMPLEXITY:
   "Time: O(n) - each element added/removed at most once per call.
    Space: O(k) for the counter."

9. CODE STRUCTURE:
   "Define at_most(k) helper. Compute at_most(k) - at_most(k-1)."

10. MENTAL TRACE:
    nums = [1, 2, 1, 2, 3], k = 2:
    at_most(2):
      right=0 (1): cnt={1}. left=0. result += 1.
      right=1 (2): cnt={1,2}. left=0. result += 2.
      right=2 (1): cnt={1,2}. left=0. result += 3.
      right=3 (2): cnt={1,2}. left=0. result += 4.
      right=4 (3): cnt={1,2,3}. > 2. shrink: cnt={2,3}, left=1. result += 4. Total: 12.
    at_most(1):
      right=0 (1): cnt={1}. result += 1.
      right=1 (2): cnt={1,2}. > 1. shrink: cnt={2}, left=1. result += 1. Total: 2.
      right=2 (1): cnt={1,2}. > 1. shrink: cnt={1}, left=2. result += 1. Total: 3.
      right=3 (2): cnt={1,2}. > 1. shrink: cnt={2}, left=3. result += 1. Total: 4.
      right=4 (3): cnt={2,3}. > 1. shrink: cnt={3}, left=4. result += 1. Total: 5.
    exactly 2 = 12 - 5 = 7. ✓
"""


# Solution 1: at_most helper (BEST)
def subarrays_with_k_distinct_v1(nums, k):
    def at_most(k_val):
        from collections import Counter
        cnt = Counter()
        left = 0
        result = 0
        for right in range(len(nums)):
            cnt[nums[right]] += 1
            while len(cnt) > k_val:
                cnt[nums[left]] -= 1
                if cnt[nums[left]] == 0:
                    del cnt[nums[left]]
                left += 1
            result += right - left + 1
        return result

    return at_most(k) - at_most(k - 1)


# Solution 2: Same logic, defaultdict
def subarrays_with_k_distinct_v2(nums, k):
    def at_most(k_val):
        from collections import defaultdict
        cnt = defaultdict(int)
        left = 0
        result = 0
        for right in range(len(nums)):
            cnt[nums[right]] += 1
            while len(cnt) > k_val:
                cnt[nums[left]] -= 1
                if cnt[nums[left]] == 0:
                    del cnt[nums[left]]
                left += 1
            result += right - left + 1
        return result

    return at_most(k) - at_most(k - 1)


# Solution 3: Direct count without helper (single pass with two pointers)
def subarrays_with_k_distinct_v3(nums, k):
    # More complex: maintain two left pointers for "at most k" and
    # "at most k-1" simultaneously.
    from collections import Counter
    n = len(nums)
    cnt1 = Counter()
    cnt2 = Counter()
    left1 = 0
    left2 = 0
    result = 0
    for right in range(n):
        cnt1[nums[right]] += 1
        cnt2[nums[right]] += 1
        while len(cnt1) > k:
            cnt1[nums[left1]] -= 1
            if cnt1[nums[left1]] == 0:
                del cnt1[nums[left1]]
            left1 += 1
        while len(cnt2) > k - 1:
            cnt2[nums[left2]] -= 1
            if cnt2[nums[left2]] == 0:
                del cnt2[nums[left2]]
            left2 += 1
        result += left2 - left1
    return result


# Solution 4: Brute force O(n^2)
def subarrays_with_k_distinct_v4(nums, k):
    n = len(nums)
    count = 0
    for i in range(n):
        seen = set()
        for j in range(i, n):
            seen.add(nums[j])
            if len(seen) == k:
                count += 1
            elif len(seen) > k:
                break
    return count


# Solution 5: Brute force with Counter
def subarrays_with_k_distinct_v5(nums, k):
    from collections import Counter
    n = len(nums)
    count = 0
    for i in range(n):
        cnt = Counter()
        for j in range(i, n):
            cnt[nums[j]] += 1
            if len(cnt) == k:
                count += 1
            elif len(cnt) > k:
                break
    return count


# Solution 6: Use numpy for vectorization
def subarrays_with_k_distinct_v6(nums, k):
    try:
        import numpy as np
        # This is hard to vectorize; just use V1.
        return subarrays_with_k_distinct_v1(nums, k)
    except ImportError:
        return subarrays_with_k_distinct_v1(nums, k)


# Solution 7: Recursive
def subarrays_with_k_distinct_v7(nums, k):
    from collections import Counter

    def at_most(k_val):
        n = len(nums)
        cnt = Counter()
        left = [0]
        result = [0]

        def helper(right):
            if right == n:
                return
            cnt[nums[right]] += 1
            while len(cnt) > k_val:
                cnt[nums[left[0]]] -= 1
                if cnt[nums[left[0]]] == 0:
                    del cnt[nums[left[0]]]
                left[0] += 1
            result[0] += right - left[0] + 1
            helper(right + 1)

        helper(0)
        return result[0]

    return at_most(k) - at_most(k - 1)


# Solution 8: at_most helper, but using dict.get
def subarrays_with_k_distinct_v8(nums, k):
    def at_most(k_val):
        cnt = {}
        left = 0
        result = 0
        for right in range(len(nums)):
            cnt[nums[right]] = cnt.get(nums[right], 0) + 1
            while len(cnt) > k_val:
                cnt[nums[left]] -= 1
                if cnt[nums[left]] == 0:
                    del cnt[nums[left]]
                left += 1
            result += right - left + 1
        return result

    return at_most(k) - at_most(k - 1)


# Solution 9: Single at_most helper, with manual loop
def subarrays_with_k_distinct_v9(nums, k):
    def at_most(k_val):
        cnt = {}
        left = 0
        result = 0
        for right, x in enumerate(nums):
            cnt[x] = cnt.get(x, 0) + 1
            # Shrink until at most k_val distinct
            while len(cnt) > k_val:
                lc = nums[left]
                cnt[lc] -= 1
                if cnt[lc] == 0:
                    del cnt[lc]
                left += 1
            result += right - left + 1
        return result

    return at_most(k) - at_most(k - 1)


# Solution 10: Final cleanest
def subarrays_with_k_distinct_v10(nums, k):
    def at_most(k_val):
        cnt = {}
        left = 0
        result = 0
        for right, x in enumerate(nums):
            cnt[x] = cnt.get(x, 0) + 1
            while len(cnt) > k_val:
                cnt[nums[left]] -= 1
                if cnt[nums[left]] == 0:
                    del cnt[nums[left]]
                left += 1
            result += right - left + 1
        return result

    return at_most(k) - at_most(k - 1)


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (Counter BEST)",          subarrays_with_k_distinct_v1),
        ("V2 (defaultdict)",           subarrays_with_k_distinct_v2),
        ("V3 (dual ptr single pass)",  subarrays_with_k_distinct_v3),
        ("V4 (brute set)",             subarrays_with_k_distinct_v4),
        ("V5 (brute Counter)",         subarrays_with_k_distinct_v5),
        ("V6 (numpy fallback)",        subarrays_with_k_distinct_v6),
        ("V7 (recursive)",             subarrays_with_k_distinct_v7),
        ("V8 (dict.get)",              subarrays_with_k_distinct_v8),
        ("V9 (manual loop)",           subarrays_with_k_distinct_v9),
        ("V10 (final clean)",          subarrays_with_k_distinct_v10),
    ]

    test_cases = [
        # (nums, k, expected)
        ([1, 2, 1, 2, 3], 2, 7),
        ([1, 2, 1, 3, 4], 3, 3),
        ([1, 2, 1, 1, 3], 3, 2),
        ([1, 1, 1, 1], 1, 10),
        ([1, 2, 3], 1, 3),
        ([1, 2, 3], 3, 1),
        ([1, 2, 3], 4, 0),
        ([1], 1, 1),
        ([1], 2, 0),
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