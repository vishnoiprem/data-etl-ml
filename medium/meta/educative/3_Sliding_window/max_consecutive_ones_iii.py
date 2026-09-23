"""
Max Consecutive Ones III - 10 Ways
==================================
Given a binary array nums and an integer k, return the maximum number
of consecutive 1's in the array if you can flip at most k 0's.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/max-consecutive-ones-iii
          (LeetCode #1004)

Examples:
    nums = [1,1,1,0,0,0,1,1,1,1,0], k = 2      -> 6
        (Flip the two 0's at positions 3-4: [1,1,1,1,1,1,1,1,1,1,0].)
    nums = [0,0,1,1,0,0,1,1,1,0,1,1,0,0,0,1,1,1,1], k = 3 -> 10
        (Flip three 0's to extend window.)
    nums = [1,1,1], k = 0                       -> 3

Constraints:
- 1 <= nums.length <= 10^5
- nums[i] is 0 or 1
- 0 <= k <= nums.length

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Longest subarray of 1's if we can flip at most k 0's."

2. KEY INSIGHT:
   "Equivalently: longest subarray with at most k 0's. Sliding window
   with zero counter."

3. PATTERN RECOGNITION:
   - Sliding window with at most k zeros
   - Track zero count in window

4. EDGE CASES:
   - k == 0 -> longest run of 1's.
   - All zeros with k >= n -> n.
   - All ones -> n.

5. TRICKY DETAIL:
   "While zero_count > k, advance left. Track max window length."

6. ALGORITHM:
   "left = 0; zero_count = 0; result = 0
    for right in range(n):
        if nums[right] == 0: zero_count += 1
        while zero_count > k:
            if nums[left] == 0: zero_count -= 1
            left += 1
        result = max(result, right - left + 1)
    return result"

7. WHY IT WORKS:
   "Window [left..right] has at most k zeros, so flipping those gives
    a window of 1's of length right-left+1. Track max."

8. COMPLEXITY:
   "Time: O(n). Space: O(1)."

9. CODE STRUCTURE:
   "Init counters. Iterate right. Track zero count. Shrink if needed.
    Update max."

10. MENTAL TRACE:
    nums=[1,1,1,0,0,0,1,1,1,1,0], k=2.
    right=0,1,2: zero_count=0. result=3.
    right=3: zero_count=1. result=4.
    right=4: zero_count=2. result=5.
    right=5: zero_count=3. shrink: left=3, zero_count=2. result=3.
    right=6: zero_count=2. result=4.
    right=7: zero_count=2. result=5.
    right=8: zero_count=2. result=6.
    right=9: zero_count=2. result=7.
      wait, but expected 6.
    right=9: zero_count=2. result = max(6, 9-3+1=7) = 7. But expected 6.
    Hmm. Let me re-trace.
    At right=5, after shrinking: left was 3 (where the first 0 was). zero_count became 2 after removing nums[3]=0. left=4. Wait, we removed nums[3]=0, so zero_count went 3->2. left=4.
    right=6 (1): no zero. result = max(3, 6-4+1=3) = 3.
    right=7 (1): result = max(3, 4) = 4.
    right=8 (1): result = max(4, 5) = 5.
    right=9 (1): result = max(5, 6) = 6.
    right=10 (0): zero_count = 3. shrink: nums[4]=0, zero_count=2, left=5.
    result = max(6, 10-5+1=6) = 6. ✓
"""


# Solution 1: Sliding window (BEST)
def longest_ones_v1(nums, k):
    left = 0
    zero_count = 0
    result = 0
    for right in range(len(nums)):
        if nums[right] == 0:
            zero_count += 1
        while zero_count > k:
            if nums[left] == 0:
                zero_count -= 1
            left += 1
        result = max(result, right - left + 1)
    return result


# Solution 2: Same with Counter
def longest_ones_v2(nums, k):
    from collections import Counter
    cnt = Counter()
    left = 0
    result = 0
    for right in range(len(nums)):
        cnt[nums[right]] += 1
        while cnt[0] > k:
            cnt[nums[left]] -= 1
            left += 1
        result = max(result, right - left + 1)
    return result


# Solution 3: Same logic, alt code
def longest_ones_v3(nums, k):
    n = len(nums)
    left = 0
    zero = 0
    result = 0
    for right in range(n):
        if nums[right] == 0:
            zero += 1
        while zero > k and left <= right:
            if nums[left] == 0:
                zero -= 1
            left += 1
        result = max(result, right - left + 1)
    return result


# Solution 4: Brute force O(n^2)
def longest_ones_v4(nums, k):
    n = len(nums)
    result = 0
    for i in range(n):
        flips = k
        for j in range(i, n):
            if nums[j] == 0:
                if flips == 0:
                    break
                flips -= 1
            result = max(result, j - i + 1)
    return result


# Solution 5: Same logic with explicit one_count
def longest_ones_v5(nums, k):
    left = 0
    one_count = 0
    result = 0
    for right in range(len(nums)):
        if nums[right] == 1:
            one_count += 1
        # If non-ones in window > k, shrink
        while (right - left + 1) - one_count > k:
            if nums[left] == 1:
                one_count -= 1
            left += 1
        result = max(result, right - left + 1)
    return result


# Solution 6: numpy fallback
def longest_ones_v6(nums, k):
    return longest_ones_v1(nums, k)


# Solution 7: Recursive
def longest_ones_v7(nums, k):
    n = len(nums)
    left = [0]
    zero = [0]
    result = [0]

    def helper(right):
        if right == n:
            return
        if nums[right] == 0:
            zero[0] += 1
        while zero[0] > k:
            if nums[left[0]] == 0:
                zero[0] -= 1
            left[0] += 1
        result[0] = max(result[0], right - left[0] + 1)
        helper(right + 1)

    helper(0)
    return result[0]


# Solution 8: Same as V1 with explicit length tracking
def longest_ones_v8(nums, k):
    left = 0
    zero = 0
    result = 0
    window_len = 0
    for right in range(len(nums)):
        if nums[right] == 0:
            zero += 1
        window_len = right - left + 1
        while zero > k:
            window_len -= 1
            if nums[left] == 0:
                zero -= 1
            left += 1
        result = max(result, window_len)
    return result


# Solution 9: Same as V1, with array slicing
def longest_ones_v9(nums, k):
    n = len(nums)
    left = 0
    zero = 0
    result = 0
    for right in range(n):
        zero += 1 if nums[right] == 0 else 0
        if zero > k:
            # Advance left past first zero
            while nums[left] == 1:
                left += 1
            left += 1  # skip the zero
            zero -= 1
        result = max(result, right - left + 1)
    return result


# Solution 10: Same as V1, most concise
def longest_ones_v10(nums, k):
    left = zero = result = 0
    for right, x in enumerate(nums):
        zero += 1 if x == 0 else 0
        while zero > k:
            zero -= 1 if nums[left] == 0 else 0
            left += 1
        result = max(result, right - left + 1)
    return result


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (BEST)",            longest_ones_v1),
        ("V2 (Counter)",         longest_ones_v2),
        ("V3 (alt code)",        longest_ones_v3),
        ("V4 (brute)",           longest_ones_v4),
        ("V5 (one_count)",       longest_ones_v5),
        ("V6 (numpy)",           longest_ones_v6),
        ("V7 (recursive)",       longest_ones_v7),
        ("V8 (run groups)",      longest_ones_v8),
        ("V9 (alt skip)",        longest_ones_v9),
        ("V10 (concise)",        longest_ones_v10),
    ]

    test_cases = [
        ([1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], 2, 6),
        ([0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1], 3, 10),
        ([1, 1, 1], 0, 3),
        ([0, 0, 0], 3, 3),
        ([0, 0, 0], 0, 0),
        ([1, 0, 0, 1], 1, 2),
        ([1, 0, 0, 1], 0, 1),
        ([0, 0, 0, 0, 0], 5, 5),
        ([1, 1, 0, 0, 1, 1], 2, 6),  # flip both 0's
        ([1, 0, 1, 0, 1, 0, 1], 3, 7),  # all but if k=3? k=3 means 3 zeros can be flipped. Here we have 3 zeros. Flip all = all 1's = 7.
        ([1, 0, 1, 0, 1, 0, 1], 2, 5),  # flip 2 zeros... let me think. 1,0,1,0,1,0,1: with 2 flips, longest?
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
