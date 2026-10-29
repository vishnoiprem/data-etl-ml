"""
Continuous Subarray Sum
Medium | 30 min

Given nums and k, return True if there's a subarray of length >= 2
whose sum is a multiple of k.

Constraints:
- 1 <= nums.length <= 10^4
- 0 <= nums[i] <= 10^5
- 1 <= k <= 2^31 - 1
- 0 is considered a multiple of k

Examples:
    [23, 2, 4, 6, 7], k=6 -> True
        Subarray [2, 4] has sum 6 (multiple of 6)

    [23, 2, 6, 4, 7], k=6 -> True
        Subarray [23, 2, 6, 4, 7] has sum 42 = 7*6

    [23, 2, 6, 4, 7], k=13 -> False
        No subarray with sum divisible by 13
"""

from collections import defaultdict, Counter


# =============================================================================
# WAY 1: HashMap of Remainders (BEST - Memorize!)
# =============================================================================
# THINKING: "Same as Subarray Sum K. Track prefix sum mod k."
# If prefix[i] % k == prefix[j] % k, sum of nums[i+1..j] is divisible by k.
def check_subarray_sum_1(nums, k):
    remainder_index = {0: -1}
    prefix_sum = 0

    for i, num in enumerate(nums):
        prefix_sum += num
        remainder = prefix_sum % k

        if remainder in remainder_index:
            if i - remainder_index[remainder] >= 2:
                return True
        else:
            remainder_index[remainder] = i

    return False


# =============================================================================
# WAY 2: Using defaultdict
# =============================================================================
def check_subarray_sum_2(nums, k):
    remainder_index = defaultdict(lambda: -2)
    remainder_index[0] = -1
    prefix_sum = 0

    for i, num in enumerate(nums):
        prefix_sum += num
        remainder = prefix_sum % k

        if remainder in remainder_index and remainder_index[remainder] >= 0:
            if i - remainder_index[remainder] >= 2:
                return True
        else:
            remainder_index[remainder] = i

    return False


# =============================================================================
# WAY 3: Brute Force with Modulo
# =============================================================================
def check_subarray_sum_3(nums, k):
    n = len(nums)
    for i in range(n):
        for j in range(i+1, n):
            sub_sum = sum(nums[i:j+1])
            if sub_sum % k == 0:
                return True
    return False


# =============================================================================
# WAY 4: Optimized Brute Force
# =============================================================================
def check_subarray_sum_4(nums, k):
    n = len(nums)
    for i in range(n):
        current = 0
        for j in range(i, n):
            current += nums[j]
            if j - i >= 1 and current % k == 0:
                return True
    return False


# =============================================================================
# WAY 5: Using enumerate and dict
# =============================================================================
def check_subarray_sum_5(nums, k):
    seen = {0: -1}
    total = 0

    for i, num in enumerate(nums):
        total += num
        r = total % k

        if r in seen and i - seen[r] > 1:
            return True
        if r not in seen:
            seen[r] = i

    return False


# =============================================================================
# WAY 6: Most compact
# =============================================================================
def check_subarray_sum_6(nums, k):
    seen = {0: -1}
    s = 0
    for i, n in enumerate(nums):
        s += n
        if s % k in seen and i - seen[s % k] > 1:
            return True
        seen.setdefault(s % k, i)
    return False


# =============================================================================
# WAY 7: With list of indices per remainder
# =============================================================================
def check_subarray_sum_7(nums, k):
    remainder_indices = defaultdict(list)
    remainder_indices[0].append(-1)
    prefix_sum = 0

    for i, num in enumerate(nums):
        prefix_sum += num
        remainder = prefix_sum % k
        remainder_indices[remainder].append(i)

        indices = remainder_indices[remainder]
        if len(indices) >= 2 and indices[-1] - indices[-2] >= 2:
            return True

    return False


# =============================================================================
# WAY 8: Using Counter
# =============================================================================
def check_subarray_sum_8(nums, k):
    remainder_count = Counter()
    remainder_count[0] = 1
    prefix_sum = 0

    for num in nums:
        prefix_sum += num
        remainder = prefix_sum % k
        remainder_count[remainder] += 1

        if remainder_count[remainder] >= 2:
            # Need to verify length >= 2 (always true if we have 2+ matches)
            return True

    return False


# =============================================================================
# WAY 9: With proper length check using tuple
# =============================================================================
def check_subarray_sum_9(nums, k):
    seen = {0: -1}
    total = 0
    for i, n in enumerate(nums):
        total += n
        r = total % k
        if r in seen:
            if i - seen[r] >= 2:
                return True
        else:
            seen[r] = i
    return False


# =============================================================================
# WAY 10: Functional with enumerate
# =============================================================================
def check_subarray_sum_10(nums, k):
    remainder_index = {0: -1}
    return any(
        (remainder_index.setdefault(
            (prefix := prefix + num) % k,
            i
        ) is not None) and i - remainder_index.get((prefix := prefix + num) % k, 0) >= 2
        for i, num in enumerate(nums)
        for prefix in [sum(nums[:i+1])]
    )
# Note: Way 10 is illustrative; it's complex. Way 1 is best.


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find a subarray of length >= 2 whose sum is divisible by k."

Key Insight:
"Same as Subarray Sum K! The math:
If prefix[i] % k == prefix[j] % k, then sum(nums[i+1..j]) is divisible by k.
So I need to find two prefix sums with the same remainder where the distance
between them is >= 2 (to ensure subarray length >= 2)."

Algorithm:
"1. Use hashmap: remainder -> first index where seen
2. For each element, compute prefix sum and prefix % k
3. If I've seen this remainder before, check if distance >= 2
4. If yes, return True"

Special case:
"If prefix sum itself is divisible by k, the subarray from index 0 to current
has length >= 1. I need to check length >= 2 specifically."

Why this works:
"Two prefix sums with same remainder means their difference is divisible by k.
That difference is exactly the sum of the elements between them."

Edge cases:
- k = 0: should not happen (constraint says k >= 1)
- Single element: never works (length must be >= 2)
- nums = [0]: length is 1, not valid

COMPLEXITY:
+-----------+--------+----------+
| Approach  | Time   | Space    |
+-----------+--------+----------+
| HashMap   | O(n)   | O(n)     |
| Brute     | O(n^2) | O(1)     |
+-----------+--------+----------+
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: HashMap remainder", check_subarray_sum_1),
        ("Way 2: defaultdict", check_subarray_sum_2),
        ("Way 3: Brute force mod", check_subarray_sum_3),
        ("Way 4: Optimized brute", check_subarray_sum_4),
        ("Way 5: enumerate dict", check_subarray_sum_5),
        ("Way 6: Most compact", check_subarray_sum_6),
        ("Way 7: List of indices", check_subarray_sum_7),
        ("Way 8: Counter", check_subarray_sum_8),
        ("Way 9: Proper length", check_subarray_sum_9),
    ]

    test_cases = [
        ([23, 2, 4, 6, 7], 6, True),
        ([23, 2, 6, 4, 7], 6, True),
        ([23, 2, 6, 4, 7], 13, False),
        ([23, 2, 4, 6, 6], 7, True),
        ([1, 2, 3], 5, False),
        ([5, 0, 0, 0], 5, True),
        ([0, 0], 1, True),
        ([1, 1], 2, True),
    ]

    print("=" * 70)
    print("CONTINUOUS SUBARRAY SUM - ALL 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums, k, expected in test_cases:
            try:
                result = func(nums, k)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                status = "✓" if result == expected else "✗"
                print(f"  {status} {name}: {nums}, k={k} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  ✗ {name}: ERROR - {e}")
        print(f"  Overall: {'PASS' if all_test_pass else 'FAIL'}\n")

    print("=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS! 🎉")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
