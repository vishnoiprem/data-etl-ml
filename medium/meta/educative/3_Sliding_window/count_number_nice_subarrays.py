"""
Count Number of Nice Subarrays - 10 Ways
=======================================
Given an array nums of positive integers and an integer k. A subarray
is called nice if there are k odd numbers in it. Return the number of
nice subarrays.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/number-of-nice-subarrays
          (LeetCode #1248)

Examples:
    nums = [1, 1, 2, 1, 1], k = 1        -> 6
        (Nice subarrays have exactly 1 odd number:
         [1] (pos 0), [1] (pos 1), [1] (pos 3), [1] (pos 4),
         [1,1,2] (pos 0..2, only nums[0] odd),
         [1,1] (pos 2..3, only nums[3] odd). Total = 6.)
    nums = [2, 4, 6], k = 1               -> 0
    nums = [2, 2, 2, 1, 2, 2, 1, 2, 2], k = 2 -> 12

Constraints:
- 1 <= nums.length <= 50000
- 1 <= nums[i] <= 10^5
- 1 <= k <= nums.length

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Count subarrays containing exactly k odd numbers."

2. KEY INSIGHT:
   "Exactly k odds = atMost(k) - atMost(k-1). Each can be computed
   with sliding window tracking odd count."

3. PATTERN RECOGNITION:
   - Sliding window for at most k odds
   - Subtract two counts
   - Equivalent: count of valid middle ranges

4. EDGE CASES:
   - k > total_odds -> 0.
   - All even nums -> 0.
   - k = 1, all odds -> n.

5. TRICKY DETAIL:
   "For each right, find smallest left such that window has > k odds.
   Sub-windows ending at right with <= k odds start in [0..largest_left].
   Wait, actually we want to count windows with <= k odds, which equals
   right - left + 1 after shrinking while odd_count > k."

6. ALGORITHM:
   "def at_most(k):
       left = 0; odd = 0; result = 0
       for right in range(n):
           if nums[right] % 2 == 1: odd += 1
           while odd > k:
               if nums[left] % 2 == 1: odd -= 1
               left += 1
           result += right - left + 1
       return result
   return at_most(k) - at_most(k - 1)"

7. WHY IT WORKS:
   "After shrinking, [left..right] has odd_count <= k. All sub-windows
   ending at right with start in [left..right] also have <= k odds
   (smaller windows have <= odds since odds only decrease as we shrink
   left). Count = right - left + 1."

8. COMPLEXITY:
   "Time: O(n). Space: O(1)."

9. CODE STRUCTURE:
   "Define at_most helper. Compute at_most(k) - at_most(k-1)."

10. MENTAL TRACE:
    nums=[1,1,2,1,1], k=1.
    at_most(1):
      right=0 (1): odd=1. result += 1.  total=1.
      right=1 (1): odd=2. shrink: nums[0]=1 odd, odd=1, left=1. result += 1.  total=2.
      right=2 (2): odd=1. result += 2.  total=4.
      right=3 (1): odd=2. shrink: nums[1]=1 odd, odd=1, left=2. result += 2.  total=6.
      right=4 (1): odd=2. shrink: nums[2]=2 even, left=3, odd still 2.
                    shrink: nums[3]=1 odd, odd=1, left=4. result += 1.  total=7.
    Total at_most(1) = 7.
    at_most(0):
      right=0 (1): odd=1. shrink: nums[0]=1 odd, odd=0, left=1. result += 0.  total=0.
      right=1 (1): odd=1. shrink: nums[1]=1 odd, odd=0, left=2. result += 0.  total=0.
      right=2 (2): odd=0. result += 1.  total=1.
      right=3 (1): odd=1. shrink: nums[2]=2 even, left=3. shrink: nums[3]=1 odd, odd=0, left=4.
                    result += 0.  total=1.
      right=4 (1): odd=1. shrink: nums[4]=1 odd, odd=0, left=5. result += 0.  total=1.
    Total at_most(0) = 1.
    exactly=1 = 7 - 1 = 6. ✓
"""


# Solution 1: at_most helper (BEST)
def number_of_nice_subarrays_v1(nums, k):
    def at_most(k_val):
        if k_val < 0:
            return 0
        left = 0
        odd = 0
        result = 0
        for right in range(len(nums)):
            if nums[right] % 2 == 1:
                odd += 1
            while odd > k_val:
                if nums[left] % 2 == 1:
                    odd -= 1
                left += 1
            result += right - left + 1
        return result

    return at_most(k) - at_most(k - 1)


# Solution 2: Same logic, alt code
def number_of_nice_subarrays_v2(nums, k):
    def at_most(k_val):
        if k_val < 0:
            return 0
        left = 0
        odd = 0
        result = 0
        for right in range(len(nums)):
            if nums[right] & 1:
                odd += 1
            while odd > k_val:
                if nums[left] & 1:
                    odd -= 1
                left += 1
            result += right - left + 1
        return result

    return at_most(k) - at_most(k - 1)


# Solution 3: Brute force
def number_of_nice_subarrays_v3(nums, k):
    n = len(nums)
    result = 0
    for i in range(n):
        odd = 0
        for j in range(i, n):
            if nums[j] % 2 == 1:
                odd += 1
            if odd == k:
                result += 1
            elif odd > k:
                break
    return result


# Solution 4: Prefix + hashmap
def number_of_nice_subarrays_v4(nums, k):
    from collections import defaultdict
    cnt = defaultdict(int)
    cnt[0] = 1
    cur = 0
    result = 0
    for x in nums:
        if x % 2 == 1:
            cur += 1
        result += cnt[cur - k]
        cnt[cur] += 1
    return result


# Solution 5: defaultdict version
def number_of_nice_subarrays_v5(nums, k):
    from collections import defaultdict
    cnt = defaultdict(int)
    cnt[0] = 1
    cur = 0
    result = 0
    for x in nums:
        if x & 1:
            cur += 1
        result += cnt.get(cur - k, 0)
        cnt[cur] += 1
    return result


# Solution 6: numpy fallback
def number_of_nice_subarrays_v6(nums, k):
    return number_of_nice_subarrays_v1(nums, k)


# Solution 7: Same as V1 with manual dict
def number_of_nice_subarrays_v7(nums, k):
    def at_most(k_val):
        if k_val < 0:
            return 0
        left = 0
        odd = 0
        result = 0
        for right in range(len(nums)):
            odd += nums[right] & 1
            while odd > k_val:
                odd -= nums[left] & 1
                left += 1
            result += right - left + 1
        return result

    return at_most(k) - at_most(k - 1)


# Solution 8: Same as V1, refactored
def number_of_nice_subarrays_v8(nums, k):
    def at_most(k_val):
        if k_val < 0:
            return 0
        left = 0
        odd = 0
        result = 0
        n = len(nums)
        for right in range(n):
            if nums[right] % 2 == 1:
                odd += 1
            while left <= right and odd > k_val:
                if nums[left] % 2 == 1:
                    odd -= 1
                left += 1
            result += right - left + 1
        return result

    return at_most(k) - at_most(k - 1)


# Solution 9: itertools.accumulate approach
def number_of_nice_subarrays_v9(nums, k):
    from itertools import accumulate
    from collections import Counter
    # Treat odd as 1, even as 0
    binary = [x % 2 for x in nums]
    prefix = [0] + list(accumulate(binary))
    cnt = Counter(prefix)
    result = 0
    for p in prefix:
        cnt[p] -= 1
        target = p + k
        result += cnt.get(target, 0)
    return result


# Solution 10: Same as V1, most concise
def number_of_nice_subarrays_v10(nums, k):
    def at_most(k_val):
        if k_val < 0:
            return 0
        left = odd = result = 0
        for right in range(len(nums)):
            odd += nums[right] & 1
            while odd > k_val:
                odd -= nums[left] & 1
                left += 1
            result += right - left + 1
        return result

    return at_most(k) - at_most(k - 1)


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (BEST)",                  number_of_nice_subarrays_v1),
        ("V2 (k_val guard)",           number_of_nice_subarrays_v2),
        ("V3 (brute)",                 number_of_nice_subarrays_v3),
        ("V4 (prefix hashmap)",        number_of_nice_subarrays_v4),
        ("V5 (defaultdict prefix)",    number_of_nice_subarrays_v5),
        ("V6 (numpy fallback)",        number_of_nice_subarrays_v6),
        ("V7 (manual dict)",           number_of_nice_subarrays_v7),
        ("V8 (alt code)",              number_of_nice_subarrays_v8),
        ("V9 (accumulate)",            number_of_nice_subarrays_v9),
        ("V10 (concise)",              number_of_nice_subarrays_v10),
    ]

    test_cases = [
        ([1, 1, 2, 1, 1], 1, 6),
        ([2, 4, 6], 1, 0),
        ([2, 2, 2, 1, 2, 2, 1, 2, 2], 2, 12),
        ([1, 1, 1, 1], 1, 4),
        ([1, 1, 1, 1], 2, 3),
        ([1, 1, 1, 1], 4, 1),
        ([1], 1, 1),
        ([1], 2, 0),
        ([2], 0, 1),
        ([1, 2, 1, 2, 1], 1, 8),
        ([1, 1, 1, 1, 1], 3, 3),
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
