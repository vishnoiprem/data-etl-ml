"""
Subarray Sum Equals K
Medium | 30 min

Given an array of integers nums and an integer k, determine the total number
of subarrays whose sum is exactly equal to k.

Constraints:
- 1 <= nums.length <= 2 * 10^4
- -1000 <= nums[i] <= 1000
- -10^7 <= k <= 10^7

Example:
    nums = [1, 1, 1], k = 2
    Output: 2
    Explanation: [1,1] at (0,1), [1,1] at (1,2)
"""

# =============================================================================
# WAY 1: Brute Force (Triple Nested Loop)
# =============================================================================
# THINKING: "Just check every single subarray."
def subarray_sum_brute(nums, k):
    count = 0
    n = len(nums)
    for i in range(n):
        for j in range(i, n):
            if sum(nums[i:j+1]) == k:
                count += 1
    return count
# Time: O(n^3) | Space: O(1)
# Lesson: Works but slow. Notice I'm calling sum() repeatedly.


# =============================================================================
# WAY 2: Brute Force Without Resumming
# =============================================================================
# THINKING: "Why do I keep adding from scratch? Just keep a running sum."
def subarray_sum_running(nums, k):
    count = 0
    n = len(nums)
    for i in range(n):
        current = 0
        for j in range(i, n):
            current += nums[j]
            if current == k:
                count += 1
    return count
# Time: O(n^2) | Space: O(1)
# Lesson: Removed the inner sum(). Saved O(n) per call.


# =============================================================================
# WAY 3: Prefix Sum Array
# =============================================================================
# THINKING: "What if I precompute ALL prefix sums once?"
def subarray_sum_prefix_array(nums, k):
    n = len(nums)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i+1] = prefix[i] + nums[i]

    count = 0
    for i in range(n):
        for j in range(i+1, n+1):
            if prefix[j] - prefix[i] == k:
                count += 1
    return count
# Time: O(n^2) | Space: O(n)
# Lesson: Now sum of nums[i..j] is O(1). Cleaner but still O(n^2).


# =============================================================================
# WAY 4: Hashmap on Prefix Sums (OPTIMAL!)
# =============================================================================
# THINKING: "For each j, I want to count how many i exist where
#           prefix[j] - prefix[i] = k.
#           That's just prefix[j] - k in a hashmap!"
def subarray_sum(nums, k):
    count = 0
    current = 0
    seen = {0: 1}

    for num in nums:
        current += num
        count += seen.get(current - k, 0)
        seen[current] = seen.get(current, 0) + 1

    return count
# Time: O(n) | Space: O(n)
# Lesson: Lookups are O(1). Big jump from O(n^2) to O(n).


# =============================================================================
# WAY 5: Using defaultdict
# =============================================================================
# THINKING: "Defaultdict is cleaner for counting."
def subarray_sum_defaultdict(nums, k):
    from collections import defaultdict
    count = 0
    current = 0
    seen = defaultdict(int)
    seen[0] = 1

    for num in nums:
        current += num
        count += seen[current - k]
        seen[current] += 1

    return count
# Time: O(n) | Space: O(n)


# =============================================================================
# WAY 6: Using Counter
# =============================================================================
# THINKING: "Same as above with Counter."
def subarray_sum_counter(nums, k):
    from collections import Counter
    count = 0
    current = 0
    seen = Counter([0])

    for num in nums:
        current += num
        count += seen[current - k]
        seen[current] += 1

    return count
# Time: O(n) | Space: O(n)


# =============================================================================
# WAY 8: Sliding Window (Only Works for Positive Numbers)
# =============================================================================
# THINKING: "If numbers were all positive, sliding window would work."
def subarray_sum_positive(nums, k):
    count = 0
    current = 0
    left = 0
    for right in range(len(nums)):
        current += nums[right]
        while current > k and left <= right:
            current -= nums[left]
            left += 1
        if current == k:
            count += 1
    return count
# Time: O(n) | Space: O(1)
# Lesson: Doesn't work with negatives! That's why we need hashmap.


# =============================================================================
# WAY 10: Using itertools.accumulate
# =============================================================================
# THINKING: "Python has a built-in for prefix sums!"
def subarray_sum_accumulate(nums, k):
    from itertools import accumulate
    count = 0
    seen = {0: 1}
    for prefix in accumulate(nums):
        count += seen.get(prefix - k, 0)
        seen[prefix] = seen.get(prefix, 0) + 1
    return count
# Time: O(n) | Space: O(n)


# =============================================================================
# WAY 14: Using List Comprehension (Brute)
# =============================================================================
def subarray_sum_comprehension(nums, k):
    n = len(nums)
    return sum(1 for i in range(n) for j in range(i+1, n+1)
               if sum(nums[i:j]) == k)


# =============================================================================
# TESTS
# =============================================================================
if __name__ == "__main__":
    test_cases = [
        ([1, 1, 1], 2, 2),
        ([1, 2, 3], 3, 2),
        ([1, -1, 1, -1, 1], 0, 6),
        ([3, 4, 7, 2, -3, 1, 4, 2], 7, 4),
        ([1], 1, 1),
        ([1], 0, 0),
        ([], 0, 0),
    ]

    print("=" * 60)
    print("SUBARRAY SUM EQUALS K - ALL APPROACHES")
    print("=" * 60)

    for nums, k, expected in test_cases:
        result = subarray_sum(nums, k)
        status = "✓" if result == expected else "✗"
        print(f"{status} nums={nums}, k={k} -> {result} (expected {expected})")

    print("\n" + "=" * 60)
    print("HOW TO THINK (THE MENTAL PROCESS)")
    print("=" * 60)
    print("""
For EVERY problem, here's the actual thinking process:

Step 1: "What's the dumbest way?"
        -> Try all combinations

Step 2: "What did I do repeatedly?"
        -> Recalculating sums? Pre-compute!

Step 3: "Can I look up info instead of searching?"
        -> Hashmap!

Step 4: "Did I find the pattern?"
        -> Yes: prefix[j] - prefix[i] = k
        -> Rearrange: prefix[i] = prefix[j] - k

UNIVERSAL PATTERN:
Most "count subarrays with property X" problems follow:
1. Define a running state (sum, product, etc.)
2. As you go, ask: "Have I seen this state before?"
3. Hashmap = quick lookup of past states
""")
