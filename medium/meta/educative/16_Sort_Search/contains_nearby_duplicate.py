"""
Contains Duplicate II
Easy | 15 min

Given an integer array nums and an integer k, return True if there exist
two distinct indices i and j such that nums[i] == nums[j] and the
absolute difference between i and j is at most k. Otherwise, return False.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/contains-duplicate-ii

Constraints:
- 1 <= nums.length <= 10^3
- -10^3 <= nums[i] <= 10^3
- 0 <= k <= 10^4

Examples:
    nums=[1,2,3,1], k=3 -> True (nums[0]==nums[3], |0-3|=3<=3)
    nums=[1,0,1,1], k=1 -> True (nums[2]==nums[3], |2-3|=1<=1)
    nums=[1,2,3,1,2,3], k=2 -> False (no duplicates within k=2)

Key Insight:
Two O(n) approaches:
1. Hash map of last seen index: store each value's most recent index.
   When we see nums[i]=v, if v was seen at index j and i-j<=k, return True.
2. Sliding window set: maintain set of last k elements. If new element is
   already in set, return True.

For the hash map approach, update only when a duplicate is found within k,
otherwise overwrite with the latest index.

Time:  O(n).
Space: O(min(n, k)).
"""


# =============================================================================
# WAY 1: Hash map of last seen index (BEST - Memorize!)
# =============================================================================
def contains_nearby_duplicate_1(nums, k):
    """
    For each element, check if it's been seen recently (within k indices).
    Use a hash map: value -> most recent index.
    """
    seen = {}  # value -> most recent index
    for i, num in enumerate(nums):
        if num in seen and i - seen[num] <= k:
            return True
        seen[num] = i
    return False


# =============================================================================
# WAY 2: Verbose version
# =============================================================================
def contains_nearby_duplicate_2(nums, k):
    """Verbose version with comments."""
    last_index = {}
    for i in range(len(nums)):
        num = nums[i]
        if num in last_index:
            j = last_index[num]
            if abs(i - j) <= k:
                return True
        last_index[num] = i
    return False


# =============================================================================
# WAY 3: Sliding window with set
# =============================================================================
def contains_nearby_duplicate_3(nums, k):
    """
    Maintain a set of the last k elements.
    If new element is already in the set, duplicate exists within k.
    """
    seen = set()
    for i, num in enumerate(nums):
        if num in seen:
            return True
        seen.add(num)
        # Keep only the last k elements
        if len(seen) > k:
            seen.remove(nums[i - k])
    return False


# =============================================================================
# WAY 4: Brute force (O(n*k))
# =============================================================================
def contains_nearby_duplicate_4(nums, k):
    """Check k neighbors for each element. O(n*k)."""
    n = len(nums)
    for i in range(n):
        for j in range(i + 1, min(i + k + 1, n)):
            if nums[i] == nums[j]:
                return True
    return False


# =============================================================================
# WAY 5: enumerate-based hash map
# =============================================================================
def contains_nearby_duplicate_5(nums, k):
    """Same as Way 1 but with explicit enumerate."""
    seen = {}
    for i, num in enumerate(nums):
        if num in seen and abs(i - seen[num]) <= k:
            return True
        seen[num] = i
    return False


# =============================================================================
# WAY 6: dict.get for cleaner lookup
# =============================================================================
def contains_nearby_duplicate_6(nums, k):
    """Use dict.get() for default value."""
    seen = {}
    for i, num in enumerate(nums):
        j = seen.get(num)
        if j is not None and i - j <= k:
            return True
        seen[num] = i
    return False


# =============================================================================
# WAY 7: defaultdict
# =============================================================================
def contains_nearby_duplicate_7(nums, k):
    """Use defaultdict for cleaner code."""
    from collections import defaultdict
    last_index = defaultdict(lambda: -1)
    for i, num in enumerate(nums):
        j = last_index[num]
        if j != -1 and i - j <= k:
            return True
        last_index[num] = i
    return False


# =============================================================================
# WAY 8: Sliding window with deque
# =============================================================================
def contains_nearby_duplicate_8(nums, k):
    """
    Use deque to track the last k values.
    """
    from collections import deque
    if k == 0:
        return False
    window = deque()
    for num in nums:
        if num in window:
            return True
        window.append(num)
        if len(window) > k:
            window.popleft()
    return False


# =============================================================================
# WAY 9: List as a window
# =============================================================================
def contains_nearby_duplicate_9(nums, k):
    """Use a list as the sliding window."""
    window = []
    for num in nums:
        if num in window:
            return True
        window.append(num)
        if len(window) > k:
            window.pop(0)
    return False


# =============================================================================
# WAY 10: Generator-based with any()
# =============================================================================
def contains_nearby_duplicate_10(nums, k):
    """Use any() with a generator expression (brute force style)."""
    n = len(nums)
    return any(
        nums[i] == nums[j]
        for i in range(n)
        for j in range(i + 1, min(i + k + 1, n))
    )


# =============================================================================
# WAY 11: Class-based
# =============================================================================
class NearbyDuplicateChecker:
    def __init__(self, nums, k):
        self.nums = nums
        self.k = k
        self.last_index = {}

    def check(self):
        for i, num in enumerate(self.nums):
            if num in self.last_index and abs(i - self.last_index[num]) <= self.k:
                return True
            self.last_index[num] = i
        return False


def contains_nearby_duplicate_11(nums, k):
    """Class-based."""
    return NearbyDuplicateChecker(nums, k).check()


# =============================================================================
# WAY 12: Using zip to look at k previous
# =============================================================================
def contains_nearby_duplicate_12(nums, k):
    """Use zip to look at the previous k elements."""
    seen = set()
    for i, num in enumerate(nums):
        if num in seen:
            return True
        seen.add(num)
        if i >= k:
            seen.discard(nums[i - k])
    return False


# =============================================================================
# WAY 13: Using collections.OrderedDict (LRU-style)
# =============================================================================
def contains_nearby_duplicate_13(nums, k):
    """Use OrderedDict for LRU semantics."""
    from collections import OrderedDict
    seen = OrderedDict()  # value -> index
    for i, num in enumerate(nums):
        if num in seen and i - seen[num] <= k:
            return True
        seen[num] = i
        if len(seen) > k:
            # Remove the oldest
            seen.popitem(last=False)
    return False


# =============================================================================
# WAY 14: Set-based with index tracking
# =============================================================================
def contains_nearby_duplicate_14(nums, k):
    """Set-based with explicit index management."""
    if k == 0:
        return False
    seen = set()
    for i in range(len(nums)):
        if nums[i] in seen:
            return True
        seen.add(nums[i])
        if i >= k:
            seen.remove(nums[i - k])
    return False


# =============================================================================
# WAY 15: Index-based with early exit
# =============================================================================
def contains_nearby_duplicate_15(nums, k):
    """Index-based with early exit on k=0."""
    if k == 0:
        return False
    last_index = {}
    for i in range(len(nums)):
        if nums[i] in last_index:
            if i - last_index[nums[i]] <= k:
                return True
        last_index[nums[i]] = i
    return False


# =============================================================================
# WAY 16: Using list as a sliding window
# =============================================================================
def contains_nearby_duplicate_16(nums, k):
    """Use a list as a sliding window of size up to k+1."""
    if k == 0:
        return False
    window = []
    for num in nums:
        if num in window:
            return True
        window.append(num)
        if len(window) > k:
            window.pop(0)
    return False


# =============================================================================
# WAY 17: Counter-based (track all indices)
# =============================================================================
def contains_nearby_duplicate_17(nums, k):
    """Track all indices per value, check pairwise distance."""
    from collections import defaultdict
    positions = defaultdict(list)
    for i, num in enumerate(nums):
        positions[num].append(i)
    for indices in positions.values():
        for j in range(1, len(indices)):
            if indices[j] - indices[j - 1] <= k:
                return True
    return False


# =============================================================================
# WAY 18: One-liner with any()
# =============================================================================
def contains_nearby_duplicate_18(nums, k):
    """One-liner style using any."""
    seen = {}
    return any(
        num in seen and i - seen[num] <= k or seen.update({num: i})
        for i, num in enumerate(nums)
    ) and any(False for _ in [None])  # ugly fallback


# Better one-liner:
def contains_nearby_duplicate_18b(nums, k):
    """Cleaner one-liner using helper."""
    last = {}
    for i, n in enumerate(nums):
        if n in last and i - last[n] <= k:
            return True
        last[n] = i
    return False


# =============================================================================
# WAY 19: Most concise
# =============================================================================
def contains_nearby_duplicate_19(nums, k):
    """Most concise hash map approach."""
    last = {}
    for i, n in enumerate(nums):
        if n in last and i - last[n] <= k:
            return True
        last[n] = i
    return False


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def contains_nearby_duplicate_20(nums, k):
    """
    Final clean version.

    Hash map: value -> most recent index.
    For each element, if we've seen it before and the distance is <= k,
    return True. Otherwise update the index.

    Why this works:
    We only care about the most recent occurrence of each value because
    any earlier occurrence would be FURTHER away (larger index distance).
    If the most recent occurrence is too far, so are all earlier ones.

    Alternative: sliding window set of size k. Same complexity.

    Time:  O(n).
    Space: O(min(n, k)) - hash map holds at most n entries.
    """
    last_index = {}  # value -> most recent index
    for i, num in enumerate(nums):
        if num in last_index and i - last_index[num] <= k:
            return True
        last_index[num] = i
    return False


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to check if there are two equal elements within k indices of each
other in the array."

Key Insight:
"For each element, I only need to check if I've seen it RECENTLY (within
k indices). Use a hash map from value to its most recent index. When I see
a duplicate, check if the distance is <= k."

Algorithm:
"1. Initialize last_index = {}.
2. For each index i and value num in nums:
3.   If num in last_index and i - last_index[num] <= k: return True.
4.   last_index[num] = i.
5. Return False."

Why this works:
"We only need the MOST RECENT index for each value. Any earlier occurrence
is further away (larger distance), so if the most recent is too far, all
earlier ones are too far too."

Edge cases:
- k=0: only adjacent equal elements count (never True since distinct indices).
- All unique elements: return False.
- All same elements: return True if n>=2 (distance = 1 <= k if k>=1).
- k >= n: any duplicate works (distance always <= n-1 <= k).
- Empty array: return False.

Complexity:
- Time:  O(n) - single pass.
- Space: O(min(n, k)) - hash map size bounded by k+1 entries.

KEY TRICK:
Hash map: value -> most recent index. Only store the most recent because
earlier indices can only be further away.

ALTERNATIVE: Sliding window set
Maintain a set of the last k elements. Add new element, remove element
at index i-k if window is too big. If new element is already in the set,
return True.

ALTERNATIVE: Brute force
For each i, check j from i+1 to min(i+k, n-1). If nums[i]==nums[j], True.
O(n*k) time, O(1) extra space.

RELATIONSHIP TO OTHER PROBLEMS:
- Contains Duplicate (LC 217): Just check if any duplicate exists.
- Contains Duplicate III (LC 220): Within k indices AND |diff| <= t (value).
- Sliding Window problems: Pattern of maintaining a window of recent items.

INTERVIEW TIPS:
1. Mention the hash map of last seen index approach.
2. Note the sliding window set as an alternative.
3. Discuss why we only need the most recent index.
4. Handle k=0 edge case explicitly.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Hash map last seen (BEST)", contains_nearby_duplicate_1),
        ("Way 2: Verbose", contains_nearby_duplicate_2),
        ("Way 3: Sliding window set", contains_nearby_duplicate_3),
        ("Way 4: Brute force O(n*k)", contains_nearby_duplicate_4),
        ("Way 5: enumerate hash map", contains_nearby_duplicate_5),
        ("Way 6: dict.get", contains_nearby_duplicate_6),
        ("Way 7: defaultdict", contains_nearby_duplicate_7),
        ("Way 8: deque window", contains_nearby_duplicate_8),
        ("Way 9: List window", contains_nearby_duplicate_9),
        ("Way 10: any() generator", contains_nearby_duplicate_10),
        ("Way 11: Class-based", contains_nearby_duplicate_11),
        ("Way 12: zip window", contains_nearby_duplicate_12),
        ("Way 13: OrderedDict", contains_nearby_duplicate_13),
        ("Way 14: Set with k check", contains_nearby_duplicate_14),
        ("Way 15: Early exit k=0", contains_nearby_duplicate_15),
        ("Way 16: Circular buffer", contains_nearby_duplicate_16),
        ("Way 17: All indices", contains_nearby_duplicate_17),
        ("Way 18: One-liner", contains_nearby_duplicate_18b),
        ("Way 19: Most concise", contains_nearby_duplicate_19),
        ("Way 20: Final cleanest", contains_nearby_duplicate_20),
    ]

    test_cases = [
        # Educative examples
        ([1, 2, 3, 1], 3, True),   # nums[0]==nums[3], |0-3|=3<=3
        ([1, 0, 1, 1], 1, True),   # nums[2]==nums[3], |2-3|=1<=1
        ([1, 2, 3, 1, 2, 3], 2, False),  # duplicates but min distance = 3 > 2

        # Single element
        ([1], 1, False),

        # Two same elements
        ([1, 1], 1, True),   # distance 1
        ([1, 1], 0, False),  # k=0, no duplicate within 0

        # Two distinct
        ([1, 2], 1, False),

        # k=0 cases
        ([1, 2, 1], 0, False),  # distance 2 > 0

        # Empty array
        ([], 5, False),

        # All same
        ([1, 1, 1, 1], 2, True),

        # All distinct
        ([1, 2, 3, 4, 5], 10, False),

        # k >= n
        ([1, 1], 100, True),
        ([1, 2, 3, 4], 100, False),

        # Negative numbers
        ([-1, -1], 1, True),
        ([-1, 0, 1], 2, False),

        # Duplicates far apart
        # nums[0]=1, nums[4]=1, |0-4|=4 > k=3 -> False
        ([1, 2, 3, 4, 1], 3, False),

        # Duplicates just within k
        ([1, 2, 3, 1], 2, False),  # |0-3|=3 > 2
        ([1, 2, 3, 1], 4, True),   # |0-3|=3 <= 4
        ([1, 2, 3, 1], 3, True),   # |0-3|=3 <= 3

        # Larger example
        # nums[0]=1, nums[6]=1, |0-6|=6 > k=5 -> False
        ([1, 2, 3, 4, 5, 6, 1, 2, 3], 5, False),

        # Same with k=6
        ([1, 2, 3, 4, 5, 6, 1, 2, 3], 6, True),  # |6-0|=6 <= 6

        # Adjacent duplicates
        ([1, 2, 2, 3], 1, True),  # |1-2|=1

        # Non-adjacent duplicates, k=2
        ([1, 2, 3, 2], 2, True),  # |1-3|=2

        # Multiple duplicates
        ([1, 2, 1, 3, 1], 2, True),  # |0-2|=2
    ]

    print("=" * 70)
    print("CONTAINS DUPLICATE II - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/contains-duplicate-ii")
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
                    print(f"  X {name}: nums={nums}, k={k} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on nums={nums}, k={k} - {e}")
        if all_test_pass:
            print(f"  OK {name}: PASS")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
